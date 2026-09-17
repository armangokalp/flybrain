"""Hız tabanlı nöron ağı: sinir kordonu modeli (Pugliese ve ark. 2025, K-025).

    τ_i dR_i/dt = max(Rmax_i · tanh(a_i / Rmax_i · (I_i + Σ_j w_ij R_j − θ_i)), 0) − R_i

    w_ij = b · (işaret × sinaps sayısı),  b = 0,03
    a_i = a'_i / s_i,   θ_i = θ'_i · s_i,   s_i = boyut_i / medyan(boyut)
    τ', a', θ', Rmax nöron başına kesik normalden örneklenir:
    τ 20 ± 2 ms, a' 1 ± 0,1, θ' 7,5 ± 0,6, Rmax 200 ± 10 Hz.

R Hz cinsinden ateşleme hızıdır; I keyfi birimli dış akımdır (Pugliese ve ark. DNg100'e
250 veriyor). Nöron boyutu büyük nöronları daha az uyarılabilir yapar.

Kelepçeli nöronlar (ör. duyu nöronları) dinamik taşımaz: hızları her adımda dışarıdan
verilen değere eşitlenir ve yalnızca çıkış bağlantılarıyla ağa katılır.

Tümleme: sabit adımlı Euler (varsayılan 0,1 ms; referans çözümle karşılaştırması
`experiments/vnc_rhythm.py` içinde).
"""

from dataclasses import dataclass

import numba as nb
import numpy as np
import scipy.sparse as sp


@dataclass(frozen=True)
class RateParams:
    tau_ms: tuple[float, float] = (20.0, 2.0)
    gain: tuple[float, float] = (1.0, 0.1)
    threshold: tuple[float, float] = (7.5, 0.6)
    r_max_hz: tuple[float, float] = (200.0, 10.0)
    w_scale: float = 0.03
    dt_ms: float = 0.1


def truncated_normal(rng: np.random.Generator, mean: float, std: float, n: int) -> np.ndarray:
    """Sıfırın altı atılan normal örnekler."""
    out = rng.normal(mean, std, n)
    bad = out <= 0
    while bad.any():
        out[bad] = rng.normal(mean, std, bad.sum())
        bad = out <= 0
    return out


def size_factors(size: np.ndarray, reference: float | None = None) -> np.ndarray:
    """Boyutu referansa (varsayılan: ağın medyanı) böler; bilinmeyen ya da sıfır boyut medyan sayılır."""
    s = np.asarray(size, dtype=np.float64).copy()
    med = np.nanmedian(np.where(s > 0, s, np.nan))
    s[~np.isfinite(s) | (s <= 0)] = med
    return s / (reference or med)


@nb.njit(cache=True, parallel=True)
def _run(n_steps, rec_every, R, indptr, indices, data, current, tau_frac, gain_over_rmax, r_max, theta,
         dynamic, clamp_idx, clamp_hz, rec_idx, rec_out, rec_start):
    n = R.shape[0]
    drive = np.empty(n)
    k = rec_start
    for step in range(n_steps):
        for c in range(clamp_idx.shape[0]):
            R[clamp_idx[c]] = clamp_hz[c]
        for i in nb.prange(n):
            if not dynamic[i]:
                continue
            acc = current[i]
            for p in range(indptr[i], indptr[i + 1]):
                acc += data[p] * R[indices[p]]
            drive[i] = acc
        for i in nb.prange(n):
            if not dynamic[i]:
                continue
            x = r_max[i] * np.tanh(gain_over_rmax[i] * (drive[i] - theta[i]))
            if x < 0.0:
                x = 0.0
            R[i] += (x - R[i]) * tau_frac[i]
        if (step + 1) % rec_every == 0 and k < rec_out.shape[0]:
            for j in range(rec_idx.shape[0]):
                rec_out[k, j] = R[rec_idx[j]]
            k += 1
    return k


class RateNetwork:
    def __init__(self, W: sp.spmatrix, size: np.ndarray, params: RateParams = RateParams(),
                 seed: int = 0, clamped: np.ndarray | None = None, size_reference: float | None = None):
        """W[post, pre] = işaret × sinaps sayısı; size: nöron başına boyut (aynı sıra).

        size_reference: boyut normalizasyonunun paydası; verilmezse ağın medyanı.
        """
        self.p = params
        self.n = W.shape[0]
        Wc = sp.csr_matrix(W, dtype=np.float64) * params.w_scale
        Wc.sort_indices()
        self._indptr = Wc.indptr.astype(np.int64)
        self._indices = Wc.indices.astype(np.int64)
        self._data = Wc.data.astype(np.float64)
        rng = np.random.default_rng(seed)
        s = size_factors(size, size_reference)
        self.tau_ms = truncated_normal(rng, *params.tau_ms, self.n)
        self.gain = truncated_normal(rng, *params.gain, self.n) / s
        self.threshold = truncated_normal(rng, *params.threshold, self.n) * s
        self.r_max = truncated_normal(rng, *params.r_max_hz, self.n)
        self._tau_frac = params.dt_ms / self.tau_ms
        self._g = self.gain / self.r_max
        self.dynamic = np.ones(self.n, dtype=np.bool_)
        if clamped is not None:
            self.dynamic[np.asarray(clamped, dtype=np.int64)] = False
        self.reset()

    def reset(self):
        self.R = np.zeros(self.n)
        self.step = 0

    @property
    def time_ms(self) -> float:
        return self.step * self.p.dt_ms

    def run(self, duration_ms: float, current: np.ndarray | None = None,
            clamp_idx: np.ndarray | None = None, clamp_hz: np.ndarray | None = None,
            record: np.ndarray | None = None, record_every_ms: float | None = None) -> np.ndarray:
        """Ağı ilerletir. record verilirse (kayıt sayısı × len(record)) hızları döndürür."""
        n_steps = int(round(duration_ms / self.p.dt_ms))
        cur = np.zeros(self.n) if current is None else np.asarray(current, dtype=np.float64)
        ci = np.zeros(0, dtype=np.int64) if clamp_idx is None else np.asarray(clamp_idx, dtype=np.int64)
        ch = np.zeros(0) if clamp_hz is None else np.asarray(clamp_hz, dtype=np.float64)
        rec = np.zeros(0, dtype=np.int64) if record is None else np.asarray(record, dtype=np.int64)
        every = max(1, int(round((record_every_ms or duration_ms) / self.p.dt_ms)))
        out = np.zeros((n_steps // every if len(rec) else 0, len(rec)))
        _run(n_steps, every, self.R, self._indptr, self._indices, self._data, cur, self._tau_frac, self._g,
             self.r_max, self.threshold, self.dynamic, ci, ch, rec, out, 0)
        self.step += n_steps
        return out
