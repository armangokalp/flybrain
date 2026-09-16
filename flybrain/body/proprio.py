"""Gövdeden beyne his (propriyosepsiyon): eklem durumundan duyu nöronu hızlarına.

Konnektomdaki bacak propriyoseptörleri, bacağın sinir kordonuna girdiği sinirden
(entryNerve) bacağa, kök tarafından (side) sağ/sola atanır. Her grup tek bir eklemi
izler ve üç kodlamadan birini kullanır:

  pozisyon   tonik; açı eşiği geçince hız sigmoid olarak artar (pençe nöronları,
             kıl plakaları). Eşikler grup içinde aralığa yayılır (aralık bölüşümü).
  hız        fazik, yöne duyarlı; açısal hız eşiği geçince doğrusal artar (kanca).
  sürat      fazik, iki yönlü; hızın mutlak değeri (topuz).

Hangi tipin neyi algıladığı (K-024):
  - Uyluk kordotonal organı (FeCO) pençe/kanca/topuz: MaleCNS eşanlamlıları.
    Bükülme mi açılma mı olduğu, Lee ve ark. (2025) FANC imzasıyla belirlenir:
    bükülme algılayıcıları tibia açıcı motor nöronlarını doğrudan uyarır ve bükücüleri
    dolaylı ketler; açılma algılayıcıları tersini yapar. Bu imza MaleCNS'te
    `experiments/proprio.py` ile doğrulanır (bkz. docs/09-govde.md 7.1).
  - Kıl plakaları eklem sınırı dedektörüdür (Pratt ve ark. 2026). Hangi eklemin hangi
    sınırını izledikleri, doğrudan uyardıkları kasların hareket yönünden çıkarılır:
    plaka, uyardığı kasların hareketinin tersi yöndeki sınırda ateşler (CxHP8'de ölçülen
    düzen; tüm plakalara genellenmesi VARSAYIM).
"""

from dataclasses import dataclass

import numpy as np

from flybrain.body.muscles import LEGS, MuscleTable
from flybrain.connectome.connectome import Connectome

# Tek bir propriyoseptörün en yüksek hızı (VARSAYIM). Ergin sinekte doğrudan ölçüm yok;
# larva kordotonal organında (lch5) tek nöron hızları 1,5-78 Hz (Warren ve Göpfert 2024).
R_MAX_HZ = 100.0

# Pençe nöronları: femur-tibia iç açısı 90°'nin altını (bükülme) ya da üstünü (açılma)
# kodlar (Mamiya ve ark. 2018; Agrawal ve ark. 2020). İç açı = π − bükülme açısı.
CLAW_SPLIT_RAD = np.pi / 2
# Kanca ve topuz nöronlarının hız eşikleri ve doygunluk aralığı (rad/s, VARSAYIM).
HOOK_THRESHOLDS = (0.5, 10.0)
CLUB_THRESHOLDS = (0.2, 10.0)
VELOCITY_SPAN = 5.0
# Kıl plakaları eklem aralığının son %30'unda ateşler (VARSAYIM).
LIMIT_FRAC = 0.3

NERVE_LEG = {"ProLN": "f", "ProAN": "f", "VProN": "f", "DProN": "f", "MesoLN": "m", "MetaLN": "h"}

# tip -> (etiket, kodlama, yön); yön +1 bükülme, -1 açılma, 0 iki yönlü
FECO = {
    "SNpp50": ("pence_bukulme", "position", +1),
    "SNpp51": ("pence_acilma", "position", -1),
    "SNpp41": ("kanca_bukulme", "velocity", +1),
    "SNpp39": ("kanca_acilma", "velocity", -1),
    "SNpp40": ("topuz", "speed", 0),
    "SNpp47": ("topuz", "speed", 0),
    "SNpp56": ("topuz", "speed", 0),
    "SNpp57": ("topuz", "speed", 0),
    "SNpp60": ("topuz", "speed", 0),
}
HAIR_PLATE = ["SNpp45", "SNpp52"]

KIND_CODE = {"position": 0, "velocity": 1, "speed": 2}


@dataclass
class ReceptorGroup:
    name: str               # "lm:pence_bukulme:SNpp50"
    kind: str               # "position" | "velocity" | "speed"
    neurons: np.ndarray     # konnektom indeksleri
    dof: str                # izlenen eklem
    sign: int               # algılanan yön (eklem açısı cinsinden); speed için 0
    thresholds: np.ndarray  # nöron başına: sign·açı (rad) ya da hız (rad/s)
    width: float
    note: str = ""


def _spread(lo: float, hi: float, n: int) -> tuple[np.ndarray, float]:
    """n eşiği [lo, hi] aralığına eşit yayar; genişlik = aralık / n."""
    step = max(hi - lo, 1e-3) / n
    return lo + step * (np.arange(n) + 0.5), step


def _leg_dofs(dofs: list[str], leg: str) -> list[int]:
    return [i for i, d in enumerate(dofs) if (d.startswith(f"{leg}_") or f"-{leg}_" in d) and "tarsus" not in d]


class Proprioception:
    """Gruplardan vektörleştirilmiş kodlayıcı."""

    def __init__(self, groups: list[ReceptorGroup], dofs: list[str]):
        self.groups = groups
        idx = np.concatenate([g.neurons for g in groups])
        order = np.argsort(idx)
        if len(np.unique(idx)) != len(idx):
            raise ValueError("bir nöron birden fazla gruba atanmış")
        pos = {d: i for i, d in enumerate(dofs)}
        rep = lambda f: np.concatenate([np.full(len(g.neurons), f(g)) for g in groups])  # noqa: E731
        self.idx = idx[order]
        self._dof = rep(lambda g: pos[g.dof]).astype(np.int64)[order]
        self._sign = rep(lambda g: g.sign).astype(np.float64)[order]
        self._kind = rep(lambda g: KIND_CODE[g.kind]).astype(np.int8)[order]
        self._thr = np.concatenate([g.thresholds for g in groups])[order]
        self._width = rep(lambda g: g.width)[order]
        self._pos = self._kind == KIND_CODE["position"]
        self._vel = self._kind == KIND_CODE["velocity"]
        self._speed = self._kind == KIND_CODE["speed"]

    def __len__(self) -> int:
        return len(self.idx)

    def rates(self, angles: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        a = angles[self._dof]
        v = velocities[self._dof]
        hz = np.empty(len(self.idx))
        p = self._pos
        z = (self._sign[p] * a[p] - self._thr[p]) / self._width[p]
        hz[p] = R_MAX_HZ / (1.0 + np.exp(-np.clip(z, -30, 30)))
        q = self._vel
        hz[q] = R_MAX_HZ * np.clip((self._sign[q] * v[q] - self._thr[q]) / self._width[q], 0.0, 1.0)
        s = self._speed
        hz[s] = R_MAX_HZ * np.clip((np.abs(v[s]) - self._thr[s]) / self._width[s], 0.0, 1.0)
        return hz

    def summary(self) -> str:
        lines = [f"{len(self.groups)} grup, {len(self.idx)} nöron"]
        for g in self.groups:
            lines.append(f"  {g.name:32s} {g.kind:8s} {len(g.neurons):3d} nöron  {g.dof} ({g.sign:+d}) {g.note}")
        return "\n".join(lines)


def _hair_plate_direction(conn: Connectome, neurons: np.ndarray, table: MuscleTable, leg: str,
                          dofs: list[str], lo: np.ndarray, hi: np.ndarray) -> tuple[int, int, str] | None:
    """Plakanın doğrudan uyardığı kasların hareket yönünden izlenen eklemi ve sınırı bulur."""
    out = np.asarray(conn.W[:, neurons].sum(axis=1)).ravel()
    leg_dofs = _leg_dofs(dofs, leg)
    pos = {d: i for i, d in enumerate(dofs)}
    drive = np.zeros(len(dofs))
    for m in table.muscles:
        if not m.name.startswith(leg + ":"):
            continue
        syn = out[m.mn].sum()
        if syn <= 0:
            continue
        for d, tau in m.torque.items():
            drive[pos[d]] += syn * tau
    # Pasif sertlik bacak eklemlerinde aynı olduğundan hareket torkla orantılıdır;
    # eklemler, aralıklarının yarısıyla ölçeklenerek karşılaştırılır.
    half = (hi - lo) / 2
    score = np.zeros(len(dofs))
    score[leg_dofs] = np.abs(drive[leg_dofs]) / np.maximum(half[leg_dofs], 1e-6)
    if score.max() == 0:
        return None
    j = int(np.argmax(score))
    share = score[j] / score.sum()
    return j, -int(np.sign(drive[j])), f"uyardığı kasların eklem payı {share:.2f}"


def build_proprioception(conn: Connectome, table: MuscleTable, dofs: list[str],
                         ranges: tuple[np.ndarray, np.ndarray, np.ndarray], flexion_sign: dict[str, int]) -> Proprioception:
    """flexion_sign: bacak -> tibia bükülmesinin eklem açısındaki işareti."""
    nn = conn.neurons
    col = lambda c: nn[c].fillna("").astype(str).to_numpy(dtype=object)  # noqa: E731
    t, side = col("type"), col("side")
    leg_of = np.array([NERVE_LEG.get(x, "") for x in col("entryNerve")], dtype=object)
    lo, hi, _ = ranges
    pos = {d: i for i, d in enumerate(dofs)}
    groups: list[ReceptorGroup] = []
    for leg in LEGS:
        here = (side == leg[0].upper()) & (leg_of == leg[1])
        tibia = f"{leg}_trochanterfemur-{leg}_tibia-pitch"
        j = pos[tibia]
        fs = flexion_sign[leg]
        for ty, (label, kind, direction) in FECO.items():
            idx = np.flatnonzero(here & (t == ty))
            if len(idx) == 0:
                continue
            sign = direction * fs
            if kind == "position":
                split = sign * fs * CLAW_SPLIT_RAD
                end = max(sign * lo[j], sign * hi[j])
                thr, width = _spread(split, max(end, split + 1e-3), len(idx))
            else:
                bounds = HOOK_THRESHOLDS if kind == "velocity" else CLUB_THRESHOLDS
                thr, _ = _spread(*bounds, len(idx))
                width = VELOCITY_SPAN
            groups.append(ReceptorGroup(f"{leg}:{label}:{ty}", kind, idx, tibia, sign, thr, width))
        for ty in HAIR_PLATE:
            idx = np.flatnonzero(here & (t == ty))
            if len(idx) == 0:
                continue
            found = _hair_plate_direction(conn, idx, table, leg, dofs, lo, hi)
            if found is None:
                continue
            k, sign, note = found
            a, b = sorted((sign * lo[k], sign * hi[k]))
            thr, width = _spread(b - LIMIT_FRAC * (b - a), b, len(idx))
            groups.append(ReceptorGroup(f"{leg}:kil_plakasi:{ty}", "position", idx, dofs[k], sign, thr, width, note))
    return Proprioception(groups, dofs)
