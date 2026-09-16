"""Beyin + kaslar + gövde: kapalı döngünün çekirdeği.

Her COUPLE_MS milisaniyede:
  1. Gövdenin eklem açıları ve hızları propriyoseptör hızlarına çevrilir.
  2. Beyin COUPLE_MS boyunca çalışır (propriyosepsiyon + dışarıdan verilen uyarım).
  3. Motor nöronların spike sayıları kas modeline gider.
  4. Kas torkları gövdeye uygulanır, fizik aynı süre boyunca ilerler.

Sineğin gözleriyle görme sonraki adımda bu döngüye eklenecek (docs/09-govde.md, 5.3).
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from flybrain.body.body import TIMESTEP_S, Body
from flybrain.body.muscles import MuscleModel, build_table
from flybrain.body.proprio import build_proprioception
from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.connectome.electrical import with_electrical
from flybrain.sim import BRAIN_PARAMS, LIFParams, Simulator, Stimulus

COUPLE_MS = 1.0
# Nötr pozdan pasif duruşa oturma süresi (ölçüm: 500 ms'den sonra eklemler < 0,002 rad/100 ms).
SETTLE_MS = 500.0


@dataclass
class Trace:
    """Bir koşunun kaydı: zaman, gövde, kas uyarılmaları, videonun kareleri."""

    t_ms: list[float] = field(default_factory=list)
    thorax: list[np.ndarray] = field(default_factory=list)
    thorax_quat: list[np.ndarray] = field(default_factory=list)
    angles: list[np.ndarray] = field(default_factory=list)
    activation: list[np.ndarray] = field(default_factory=list)
    mn_spikes: list[np.ndarray] = field(default_factory=list)  # önceki kayıttan bu yana, muscles.mn sırası
    proprio_spikes: list[np.ndarray] = field(default_factory=list)  # önceki kayıttan bu yana, proprio.idx sırası
    frames: dict[str, list[np.ndarray]] = field(default_factory=dict)

    def arrays(self) -> dict[str, np.ndarray]:
        return {
            "t_ms": np.array(self.t_ms),
            "thorax": np.array(self.thorax),
            "thorax_quat": np.array(self.thorax_quat),
            "angles": np.array(self.angles),
            "activation": np.array(self.activation),
            "mn_spikes": np.array(self.mn_spikes),
            "proprio_spikes": np.array(self.proprio_spikes),
        }


class EmbodiedFly:
    def __init__(
        self,
        conn: Connectome | None = None,
        seed: int = 0,
        params: LIFParams = BRAIN_PARAMS,
        std_exempt: np.ndarray | None = None,
        camera_res: tuple[int, int] = (360, 480),
        electrical: bool = True,
        proprioception: bool = True,
    ):
        self.conn = conn or load_connectome()
        self.gap_junctions = []
        if electrical:
            self.conn, gap_exempt, self.gap_junctions = with_electrical(self.conn, params)
            std_exempt = gap_exempt if std_exempt is None else np.union1d(std_exempt, gap_exempt)
        self.body = Body(camera_res=camera_res)
        self.table = build_table(self.conn, self.body.passive)
        self.muscles = MuscleModel(self.table, self.body.dofs, self.body.dof_ranges())
        self.proprio = None
        if proprioception:
            flex = {leg: v["tibia_flexion_sign"] for leg, v in self.body.geom["nmf"]["legs"].items()}
            self.proprio = build_proprioception(self.conn, self.table, self.body.dofs,
                                                self.body.dof_ranges(), flex)
        self.brain = Simulator(self.conn, params, seed=seed, std_exempt=std_exempt)
        self._steps = int(round(COUPLE_MS / 1000 / TIMESTEP_S))
        self._joint_index = {n: i for i, n in enumerate(self.body.joint_names)}

    def joint(self, name: str) -> int:
        return self._joint_index[name]

    def reset(self, settle: bool = True):
        """Beyni ve gövdeyi sıfırlar; gövde pasif duruşuna oturana kadar ikisi birlikte çalışır.

        Oturma sırasında propriyosepsiyon kapalıdır: model sineği havada nötr pozda
        başlatır ve zemine iniş gerçek bir durum değildir. Beyin bu sürede girdi almaz.
        """
        self.brain.reset()
        self.body.reset()
        self.muscles.reset()
        if settle:
            proprio, self.proprio = self.proprio, None
            try:
                self.run(SETTLE_MS)
            finally:
                self.proprio = proprio

    def run(
        self,
        duration_ms: float,
        stim: Stimulus | None = None,
        cameras: tuple[str, ...] = (),
        fps: float = 30.0,
        trace: Trace | None = None,
        record_every_ms: float = 5.0,
        on_step: Callable[["EmbodiedFly"], None] | None = None,
    ) -> Trace:
        """on_step: her eşleşme adımında fizikten önce çağrılır (deneylerde dış prob için)."""
        trace = trace or Trace()
        for c in cameras:
            trace.frames.setdefault(c, [])
        n = int(round(duration_ms / COUPLE_MS))
        frame_every = max(1, int(round(1000 / fps / COUPLE_MS)))
        rec_every = max(1, int(round(record_every_ms / COUPLE_MS)))
        mn = self.muscles.mn
        acc = np.zeros(len(mn), dtype=np.int32)
        pr = self.proprio.idx if self.proprio is not None else np.zeros(0, dtype=np.int64)
        pr_acc = np.zeros(len(pr), dtype=np.int32)
        for k in range(n):
            angles = self.body.dof_angles()
            drive = stim
            if self.proprio is not None:
                hz = self.proprio.rates(angles, self.body.dof_velocities())
                drive = Stimulus(pr, hz) if stim is None or len(stim) == 0 else Stimulus.of(np.r_[pr, stim.idx], np.r_[hz, stim.hz])
            result = self.brain.run(COUPLE_MS, drive).counts
            counts = result[mn]
            acc += counts
            pr_acc += result[pr]
            torques = self.muscles.step(counts, COUPLE_MS, angles)
            if on_step is not None:
                on_step(self)
            self.body.step(torques, self._steps)
            if cameras and k % frame_every == 0:
                for c in cameras:
                    trace.frames[c].append(self.body.render(c))
            if k % rec_every == 0:
                s = self.body.state()
                trace.t_ms.append(self.brain.time_ms)
                trace.thorax.append(s.thorax_pos)
                trace.thorax_quat.append(s.thorax_quat)
                trace.angles.append(s.joint_angles)
                trace.activation.append(self.muscles.activation.copy())
                trace.mn_spikes.append(acc.copy())
                trace.proprio_spikes.append(pr_acc.copy())
                acc[:] = 0
                pr_acc[:] = 0
        return trace
