"""Sızıntılı integrate-and-fire (LIF) tüm beyin simülasyonu.

Model Shiu ve ark. (2024) ile aynıdır:

    dv/dt = (v_rest - v + g - a) / tau_m  (refrakter sürede donar)
    dg/dt = -g / tau_syn
    da/dt = -a / tau_adapt                (a = 0: Shiu modeli)
    v > v_th  ->  spike;  v = v_reset, g = 0, refrakter başlar
    spike     ->  gecikme sonrası  g[post] += W[post, pre] * w_syn
    Poisson   ->  v += poisson_kick

İsteğe bağlı kısa süreli sinaptik depresyon (Tsodyks-Markram tipi, presinaptik):
her nöronun bir kaynak değişkeni x vardır (dinlenimde 1). Spike anında iletilen
ağırlık w·x olur, ardından x -= U·x; x, tau_rec ile 1'e geri döner. U = 0 iken
model Shiu ve ark. ile birebir aynıdır. `std_skip_sensory` ile duyu nöronları
muaf tutulabilir: onların Poisson hızı zaten duyu organının etkin çıktısıdır ve
bu nöronlar girdi almadıkları için yankı döngülerinin parçası değildir.

İsteğe bağlı ateşleme hızı adaptasyonu: her spike a'yı `adapt_mv` kadar artırır
(kalsiyumla aktive olan potasyum akımının basit modeli). adapt_mv = 0 iken
model Shiu ve ark. ile birebir aynıdır.

Bir zaman adımındaki işlem sırası Brian2'nin varsayılan sıralamasını izler:
durum güncellemesi, eşik, gecikmeli sinaps iletimi ve Poisson girdisi, sıfırlama.
Denklemler doğrusal olduğundan adım başına tam (analitik) çözüm kullanılır.

Simülasyon olay güdümlüdür: her adımda yalnızca ateşleyen nöronların çıkış
sütunları toplanır. Beyin durumu `run` çağrıları arasında korunur.
"""

from dataclasses import dataclass

import numba as nb
import numpy as np

from flybrain.connectome.connectome import Connectome


@dataclass(frozen=True)
class LIFParams:
    dt_ms: float = 0.1
    v_rest_mv: float = -52.0
    v_reset_mv: float = -52.0
    v_thresh_mv: float = -45.0
    tau_m_ms: float = 20.0
    tau_syn_ms: float = 5.0
    t_ref_ms: float = 2.2
    delay_ms: float = 1.8
    w_syn_mv: float = 0.275
    poisson_kick_mv: float = 0.275 * 250  # Shiu ve ark.: w_syn × 250; w_syn'den bağımsız tutulur
    std_u: float = 0.0          # sinaptik depresyon: spike başına tüketilen kaynak oranı
    std_tau_ms: float = 500.0   # sinaptik depresyon: kaynağın geri dolma zaman sabiti
    std_skip_sensory: bool = False  # duyu nöronlarını depresyondan muaf tut
    adapt_mv: float = 0.0       # adaptasyon: spike başına a artışı
    adapt_tau_ms: float = 200.0 # adaptasyon: a'nın sönme zaman sabiti


@dataclass
class RunResult:
    counts: np.ndarray        # nöron başına spike sayısı
    duration_ms: float
    spike_steps: np.ndarray   # kaydedilen nöronların spike adımları (mutlak)
    spike_neurons: np.ndarray
    record_overflow: bool

    @property
    def rates_hz(self) -> np.ndarray:
        return self.counts / (self.duration_ms / 1000.0)


@nb.njit(cache=True)
def _run(
    n_steps, t0, seed,
    v, g, ref, ring_idx, ring_fac, ring_n, scratch,
    x, t_last, std_u, std_k,
    a, ea, ca, adapt,
    indptr, indices, wdata,
    stim_idx, stim_p, kick,
    em, es, cg, v_rest, v_reset, v_th, ref_steps,
    counts, rec_mask, rec_steps, rec_neurons,
):
    np.random.seed(seed)
    n = v.shape[0]
    depth = ring_n.shape[0]
    n_rec = 0
    overflow = False
    for s in range(n_steps):
        t = t0 + s

        # Durum güncellemesi ve eşik aynı döngüde: eşik, güncellenmiş v'ye bakar.
        n_new = 0
        for i in range(n):
            gi = g[i]
            ai = a[i]
            if ref[i] > 0:
                ref[i] -= 1
            else:
                v[i] = v_rest + (v[i] - v_rest) * em + gi * cg - ai * ca
            g[i] = gi * es
            a[i] = ai * ea
            if ref[i] == 0 and v[i] > v_th:
                scratch[n_new] = i
                n_new += 1

        # `depth` adım önce ateşleyenlerin iletimi.
        slot = t % depth
        for k in range(ring_n[slot]):
            pre = ring_idx[slot, k]
            fac = ring_fac[slot, k]
            for j in range(indptr[pre], indptr[pre + 1]):
                g[indices[j]] += wdata[j] * fac

        for k in range(stim_idx.shape[0]):
            if np.random.random() < stim_p[k]:
                v[stim_idx[k]] += kick

        # Sıfırlama; yeni spike'lar `depth` adım sonra iletilmek üzere halkaya yazılır.
        for k in range(n_new):
            i = scratch[k]
            v[i] = v_reset
            g[i] = 0.0
            ref[i] = ref_steps
            a[i] += adapt
            counts[i] += 1
            ring_idx[slot, k] = i
            if std_u[i] > 0.0:
                xi = 1.0 - (1.0 - x[i]) * np.exp(-(t - t_last[i]) * std_k)
                ring_fac[slot, k] = xi
                x[i] = xi * (1.0 - std_u[i])
                t_last[i] = t
            else:
                ring_fac[slot, k] = 1.0
            if rec_mask[i]:
                if n_rec < rec_steps.shape[0]:
                    rec_steps[n_rec] = t
                    rec_neurons[n_rec] = i
                    n_rec += 1
                else:
                    overflow = True
        ring_n[slot] = n_new
    return n_rec, overflow


class Simulator:
    def __init__(self, conn: Connectome, params: LIFParams = LIFParams(), seed: int = 0):
        self.conn = conn
        self.p = params
        self.n = conn.n
        W = conn.W
        self._indptr = W.indptr.astype(np.int64)
        self._indices = W.indices.astype(np.int32)
        self._wdata = W.data.astype(np.float64) * params.w_syn_mv

        dt = params.dt_ms
        self._em = np.exp(-dt / params.tau_m_ms)
        self._es = np.exp(-dt / params.tau_syn_ms)
        # dv/dt = (v_rest - v + g)/tau_m, g = g0·exp(-t/tau_s) denkleminin tam çözümündeki g katsayısı
        self._cg = params.tau_syn_ms / (params.tau_syn_ms - params.tau_m_ms) * (self._es - self._em)
        self._ea = np.exp(-dt / params.adapt_tau_ms)
        self._ca = params.adapt_tau_ms / (params.adapt_tau_ms - params.tau_m_ms) * (self._ea - self._em)
        self._ref_steps = int(round(params.t_ref_ms / dt))
        self._std_u = np.full(self.n, params.std_u)
        if params.std_skip_sensory:
            sensory = conn.neurons.superclass.fillna("").str.contains("sensory").to_numpy()
            self._std_u[sensory] = 0.0
        self._depth = int(round(params.delay_ms / dt))
        self._kick = params.poisson_kick_mv

        self._rng = np.random.default_rng(seed)
        self.reset()

    def reset(self) -> None:
        """Beyni dinlenim durumuna döndürür."""
        self.v = np.full(self.n, self.p.v_rest_mv)
        self.g = np.zeros(self.n)
        self.ref = np.zeros(self.n, dtype=np.int32)
        self._ring_idx = np.zeros((self._depth, self.n), dtype=np.int32)
        self._ring_fac = np.ones((self._depth, self.n))
        self._ring_n = np.zeros(self._depth, dtype=np.int64)
        self._scratch = np.zeros(self.n, dtype=np.int32)
        self.x = np.ones(self.n)
        self.a = np.zeros(self.n)
        self._t_last = np.zeros(self.n, dtype=np.int64)
        self.step = 0

    @property
    def time_ms(self) -> float:
        return self.step * self.p.dt_ms

    def run(
        self,
        duration_ms: float,
        stim_idx: np.ndarray | None = None,
        stim_hz: np.ndarray | float | None = None,
        record: np.ndarray | None = None,
        max_records: int = 1_000_000,
    ) -> RunResult:
        """Beyni `duration_ms` boyunca çalıştırır.

        stim_idx: Poisson girdisi alan nöronların indeksleri.
        stim_hz: her biri için hız (tek sayı ya da dizi).
        record: spike zamanları kaydedilecek nöronların indeksleri.
        """
        n_steps = int(round(duration_ms / self.p.dt_ms))
        if stim_idx is None:
            stim_idx = np.zeros(0, dtype=np.int64)
            stim_p = np.zeros(0)
        else:
            stim_idx = np.asarray(stim_idx, dtype=np.int64)
            hz = np.broadcast_to(np.asarray(stim_hz, dtype=np.float64), stim_idx.shape)
            stim_p = hz * self.p.dt_ms / 1000.0

        rec_mask = np.zeros(self.n, dtype=np.bool_)
        if record is not None:
            rec_mask[np.asarray(record)] = True
        cap = max_records if record is not None else 0
        rec_steps = np.zeros(cap, dtype=np.int64)
        rec_neurons = np.zeros(cap, dtype=np.int32)
        counts = np.zeros(self.n, dtype=np.int32)

        seed = int(self._rng.integers(2**31))
        n_rec, overflow = _run(
            n_steps, self.step, seed,
            self.v, self.g, self.ref, self._ring_idx, self._ring_fac, self._ring_n, self._scratch,
            self.x, self._t_last, self._std_u, self.p.dt_ms / self.p.std_tau_ms,
            self.a, self._ea, self._ca, self.p.adapt_mv,
            self._indptr, self._indices, self._wdata,
            stim_idx, stim_p, self._kick,
            self._em, self._es, self._cg,
            self.p.v_rest_mv, self.p.v_reset_mv, self.p.v_thresh_mv, self._ref_steps,
            counts, rec_mask, rec_steps, rec_neurons,
        )
        self.step += n_steps
        return RunResult(
            counts=counts,
            duration_ms=n_steps * self.p.dt_ms,
            spike_steps=rec_steps[:n_rec],
            spike_neurons=rec_neurons[:n_rec],
            record_overflow=bool(overflow),
        )
