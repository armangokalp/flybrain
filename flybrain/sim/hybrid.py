"""Beyin (LIF, spike) + sinir kordonu (hız modeli) melezi (K-025).

Bölünme:
  - Hız modeli (`rate.py`): bacak motor ağı — bacak motor nöronları ve onların premotor
    nöronları (`connectome/motor_network.py`; inen ve duyu nöronları hariç).
  - LIF (`lif.py`): geri kalan her şey — beyin, inen nöronlar, kanat/halter/karın/boyun
    devreleri (bu ağlar hız modelinde kararsız; docs/09-govde.md 8).

Sınırlar (her eşleşme adımında):
  - LIF → hız ağı: hız ağına sinaps yapan LIF nöronlarının (çoğu inen nöron) spike'ları
    üstel süzgeçle hıza çevrilir ve hız ağına kelepçeli düğüm olarak girer.
  - Duyu → hız ağı: kodlayıcıların hızları (ör. propriyosepsiyon) doğrudan kelepçelenir.
    Aynı duyu nöronları LIF'te de aynı hızla Poisson girdisi alır (beyne giden dalları için).
  - Hız ağı → LIF: LIF nöronlarına sinaps yapan hız ağı nöronları LIF'te yalnızca Poisson
    girdisiyle, hız modelindeki hızlarında ateşler. LIF'te hız ağı nöronlarının girdi
    satırları sıfırdır; iç dinamikleri yalnızca hız modelindedir.
  - Hız ağı nöronlarının spike sayıları (motor nöronlar dahil) hızlarından Poisson olarak
    örneklenir; LIF'e ateşleyenler için LIF'teki gerçek spike'lar kullanılır.
  - Dış uyarım: LIF nöronlarına Poisson; hız ağı nöronlarına verilen uyarım o nöronun
    hızını uyarım hızına kelepçeler (ör. motor nöronun doğrudan uyarılması).
"""

import numpy as np
import scipy.sparse as sp

from flybrain.connectome import motor_network
from flybrain.connectome.connectome import Connectome
from flybrain.connectome.sizes import with_fallback
from flybrain.sim.lif import BRAIN_PARAMS, LIFParams, Simulator
from flybrain.sim.rate import RateNetwork, RateParams
from flybrain.sim.stimulus import Stimulus

RATE_SUPERCLASSES = ("vnc_intrinsic", "vnc_motor", "ascending_neuron", "vnc_efferent", "efferent_ascending")
# LIF spike'larını hız ağının girdisi olan hıza çeviren süzgecin zaman sabiti (VARSAYIM).
# Hız modeli girdisini bir popülasyon hızı olarak yorumlar; tek bir inen nöronun 15 Hz'lik
# spike dizisi 20 ms'lik süzgeçle 90 Hz'e varan anlık sıçramalar üretir ve bacak ağını kalıcı
# doyuma iter. 300 ms (15 Hz'de ~4-5 spike aralığı) ritmi korur (docs/09-govde.md 8).
SPIKE_FILTER_MS = 300.0


class HybridCNS:
    def __init__(self, conn: Connectome, params: LIFParams = BRAIN_PARAMS, seed: int = 0,
                 std_exempt: np.ndarray | None = None, rate_params: RateParams = RateParams(),
                 sensors: np.ndarray | None = None, spike_filter_ms: float = SPIKE_FILTER_MS,
                 cut_axon_feedback: bool = True):
        """sensors: hızı kodlayıcılardan gelecek duyu nöronları (sıralı indeksler)."""
        self.spike_filter_ms = spike_filter_ms
        self.conn = conn
        n = conn.n
        sup = conn.neurons.superclass.fillna("").astype(str).to_numpy(dtype=object)
        roles = motor_network.load(conn)
        members = conn.index_of(roles.bodyId.to_numpy())
        in_rate = np.zeros(n, dtype=bool)
        in_rate[members] = True
        in_rate &= np.isin(sup, RATE_SUPERCLASSES)
        is_sensory = np.char.find(sup.astype(str), "sensory") >= 0
        self.in_rate = in_rate
        self.rate_neurons = np.flatnonzero(in_rate)
        W = conn.W.tocsr()

        pre = np.unique(W[self.rate_neurons].indices)
        outside = pre[~in_rate[pre]]
        self.sensors = np.zeros(0, dtype=np.int64) if sensors is None else np.asarray(sensors, dtype=np.int64)
        self.from_sensors = np.intersect1d(outside, self.sensors)
        self.from_brain = outside[~is_sensory[outside]]
        self.nodes = np.r_[self.rate_neurons, self.from_brain, self.from_sensors]
        self.pos = np.full(n, -1, dtype=np.int64)
        self.pos[self.nodes] = np.arange(len(self.nodes))
        nv = len(self.rate_neurons)
        keep_rows = np.zeros(len(self.nodes))
        keep_rows[:nv] = 1.0
        W_nodes = sp.diags(keep_rows) @ W[self.nodes][:, self.nodes]

        size, self.size_source = with_fallback(conn.neurons)
        size = size.to_numpy()
        reference = float(np.median(size[members]))
        self.rate = RateNetwork(W_nodes, size[self.nodes], rate_params, seed=seed,
                                clamped=np.arange(nv, len(self.nodes)), size_reference=reference)

        # LIF: hız ağı nöronlarının girdi satırları sıfır.
        W_lif = (sp.diags((~in_rate).astype(conn.W.dtype), dtype=conn.W.dtype) @ conn.W).tocsc()
        if cut_axon_feedback:
            # Hız ağı nöronlarının inen nöronlara sinapsları kordonda, inen nöronun akson uçlarında.
            # Tek bölmeli LIF'te bu sinapslar beyindeki spike başlangıç bölgesini de susturur;
            # bu yapaylığı önlemek için kesilir (VARSAYIM, docs/09-govde.md 8).
            dn = sup == "descending_neuron"
            W_lif = W_lif.tocsr()
            W_lif = W_lif - sp.diags(dn.astype(W_lif.dtype), dtype=W_lif.dtype) @ W_lif @ sp.diags(in_rate.astype(W_lif.dtype), dtype=W_lif.dtype)
            W_lif = W_lif.tocsc()
        W_lif.eliminate_zeros()
        W_lif.sort_indices()
        self.brain = Simulator(Connectome(conn.neurons, W_lif, conn.label + "+hibrit"), params,
                               seed=seed, std_exempt=std_exempt)
        Wc = conn.W.tocsc()
        to_brain = np.asarray(abs(Wc[~in_rate][:, self.rate_neurons]).sum(axis=0)).ravel() > 0
        self.to_brain = self.rate_neurons[to_brain]
        self._to_brain_pos = self.pos[self.to_brain]
        self._from_brain_pos = self.pos[self.from_brain]
        self._from_sensors_pos = self.pos[self.from_sensors]
        self._sensor_sel = np.searchsorted(self.sensors, self.from_sensors)
        self._sample = np.ones(nv, dtype=bool)
        self._sample[np.searchsorted(self.rate_neurons, self.to_brain)] = False
        self._rng = np.random.default_rng(seed + 1)
        self.reset()

    def reset(self):
        self.brain.reset()
        self.rate.reset()
        self.spike_rate = np.zeros(len(self.from_brain))

    @property
    def time_ms(self) -> float:
        return self.brain.time_ms

    @property
    def network_rates(self) -> np.ndarray:
        """Hız ağı nöronlarının anlık hızları (Hz), self.rate_neurons sırasıyla."""
        return self.rate.R[:len(self.rate_neurons)]

    def step(self, dt_ms: float, stim: Stimulus | None = None, sensor_hz: np.ndarray | None = None) -> np.ndarray:
        """LIF ve hız ağını dt_ms ilerletir; tüm nöronlar için spike sayılarını döndürür."""
        nv = len(self.rate_neurons)
        R = self.rate.R
        parts_idx = [self.to_brain]
        parts_hz = [R[self._to_brain_pos]]
        forced_pos = np.zeros(0, dtype=np.int64)
        forced_hz = np.zeros(0)
        if stim is not None and len(stim):
            in_net = self.in_rate[stim.idx]
            forced_pos = self.pos[stim.idx[in_net]]
            forced_hz = stim.hz[in_net]
            parts_idx.append(stim.idx[~in_net])
            parts_hz.append(stim.hz[~in_net])
        if sensor_hz is not None and len(self.sensors):
            parts_idx.append(self.sensors)
            parts_hz.append(sensor_hz)
        drive = Stimulus.of(np.concatenate(parts_idx), np.concatenate(parts_hz))
        counts = self.brain.run(dt_ms, drive).counts

        inst = counts[self.from_brain] * (1000.0 / dt_ms)
        self.spike_rate += (inst - self.spike_rate) * (1.0 - np.exp(-dt_ms / self.spike_filter_ms))
        sens = np.zeros(len(self.from_sensors)) if sensor_hz is None else sensor_hz[self._sensor_sel]
        clamp_idx = np.r_[self._from_brain_pos, self._from_sensors_pos, forced_pos]
        clamp_hz = np.r_[self.spike_rate, sens, forced_hz]
        if len(forced_pos):
            self.rate.dynamic[forced_pos] = False
        self.rate.run(dt_ms, clamp_idx=clamp_idx, clamp_hz=clamp_hz)
        if len(forced_pos):
            self.rate.dynamic[forced_pos] = True

        lam = np.maximum(R[:nv], 0.0) * (dt_ms / 1000.0)
        sampled = self._rng.poisson(lam[self._sample])
        counts[self.rate_neurons[self._sample]] = sampled
        return counts
