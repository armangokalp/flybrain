"""Motor nöron → kas → eklem torku.

Eşleme tablosu anatomiye dayanır ve davranışa bakılarak ayarlanmaz (K-019).
Geometri (moment kolları, kuvvetler, hareket yönleri) `muscle_geometry.json`
dosyasından gelir; bu dosya `python -m flybrain.body.derive` ile üretilir.

Kas modeli:
  - Her motor nöronun bir seğirme durumu x ∈ [0, 1] vardır. Her spike x'i
    Δ·(1 − x) kadar artırır; x, τ_gevşeme ile söner.
  - Kasın uyarılması, onu süren motor nöronların x ortalamasıdır.
  - Kuvvet uyarılmayı τ_yükselme gecikmesiyle izler.
  - Tork = kuvvet × moment kolu (bacaklar) ya da en büyük tork × uyarılma (diğerleri).
  - Boy–kuvvet: kas tamamen kısaldığında kuvvet üretemez. Sınırlı eklemlerde, eklem kasın
    çektiği yöndeki sınıra yaklaştıkça (aralığın son FL_MARGIN kadarı) tork doğrusal olarak
    sıfıra iner. Kas boyu, eklem açısının fonksiyonu olarak yaklaşıklanır.

Kaynağı olmayan her parametre VARSAYIM olarak işaretlidir ve docs/09-govde.md'de listelenir.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from flybrain.connectome.connectome import Connectome

GEOMETRY_PATH = Path(__file__).with_name("muscle_geometry.json")

LEG_SUBCLASS = {"fl": "f", "ml": "m", "hl": "h"}
LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")

# Kas seğirmesi. VARSAYIM: Δ ve τ değerleri böcek kaslarının tipik aralığından seçildi.
# TTM tek seğirmeli bir kastır: tek spike tam seğirme verir (Zumstein ve ark. 2004).
TWITCH_GAIN = 0.3
TWITCH_GAIN_TTM = 1.0
RELAX_MS = 40.0
FL_MARGIN = 0.25  # aralığın oranı (VARSAYIM)
RISE_MS = 8.2  # TTM'de ölçülen tepeye ulaşma süresi; diğer kaslara da uygulanıyor (VARSAYIM)

# Kas-iskelet modeli olmayan eklemler için en büyük tork = pasif sertlik × bu açı.
# VARSAYIM: tam uyarılma eklemi yaklaşık bu kadar döndürür.
RANGE_RAD = {
    "rostrum": 1.0,
    "haustellum": 1.0,
    "head": 0.35,
    "wing": 1.2,
    "abdomen": 0.15,  # segment başına; 5 segment toplamı ~0,75 rad
    "tarsus": 0.5,
}

# Bacak motor nöron tipi → kas-iskelet modelindeki kas(lar).
# "Acc. ti flexor" modelde ayrı kas olarak yok; tibia bükücüsü havuzuna katılır.
# "Tergotr." ve "Sternotrochanter" modelde tek bir birleşik kasın a/b parçaları.
LEG_MN_TO_MUSCLES = {
    "Tergopleural/Pleural promotor MN": ["tergopleural_promotor_a", "tergopleural_promotor_b", "pleural_promotor"],
    "Pleural remotor/abductor MN": ["pleural_remotor_and_abductor"],
    "Sternal anterior rotator MN": ["sternal_anterior_rotator"],
    "Sternal posterior rotator MN": ["sternal_posterior_rotator"],
    "Sternal adductor MN": ["sternal_adductor"],
    "Tergotr. MN": ["sterno-tergo-trochanter_extensor_a", "sterno-tergo-trochanter_extensor_b"],
    "Sternotrochanter MN": ["sterno-tergo-trochanter_extensor_a", "sterno-tergo-trochanter_extensor_b"],
    "Tr extensor MN": ["trochanter_extensor"],
    "Tr flexor MN": ["trochanter_flexor_a", "trochanter_flexor_b"],
    "Acc. tr flexor MN": ["accesory_trochanter_flexor"],
    "Ti extensor MN": ["Tibia_extensor_93932"],
    "Ti flexor MN": ["Tibia_flex_93434"],
    "Acc. ti flexor MN": ["Tibia_flex_93434"],
}
# Tarsus: kas-iskelet modelinde yok. Yön anatomiden (aşağı bükme / kaldırma),
# büyüklük RANGE_RAD["tarsus"] varsayımından. ltm (uzun tendon kası) pençeyi büker;
# burada tarsusu aşağı büken kaslara katılır.
TARSUS_MN = {
    "Ta depressor MN": +1,
    "ltm MN": +1,
    "ltm1-tibia MN": +1,
    "ltm2-femur MN": +1,
    "Ta levator MN": -1,
}
# Hortum (McKellar ve ark. 2020). Labellum ve yutak kasları gövde modelinde yok.
PROBOSCIS_MN = {
    "MN9": {"rostrum": +1, "haustellum": +1},   # rostrum ileri + haustellum açılma
    "MN4a": {"haustellum": +1},
    "MN4b": {"haustellum": +1},
    "MN1": {"rostrum": -1},                     # geri çekme
    "MN2Da": {"rostrum": -1},
    "MN2Db": {"rostrum": -1},
    "MN2V": {"rostrum": -1},
    "MN3L": {"haustellum": -1},                 # haustellum bükme
    "MN3M": {"haustellum": -1},
}
# Kanat yönlendirme kasları (O'Sullivan ve ark. 2018: kanat açılmasını düzenler).
# VARSAYIM: üçüncü aksiller (iii) kaslar kanadı katlar, diğerleri açar.
WING_EXTEND = ["b1 MN", "b2 MN", "b3 MN", "i1 MN", "i2 MN", "hg1 MN", "hg2 MN", "hg3 MN", "hg4 MN",
               "ps1 MN", "ps2 MN", "tp1 MN", "tp2 MN", "tpn MN"]
WING_FOLD = ["iii1 MN", "iii3 MN"]


@dataclass
class Muscle:
    name: str
    mn: np.ndarray                     # konnektom indeksleri
    torque: dict[str, float]           # eklem serbestlik derecesi → tam uyarılmada tork (µN·mm)
    gain: float = TWITCH_GAIN


@dataclass
class MuscleTable:
    muscles: list[Muscle]
    unmapped: dict[str, int] = field(default_factory=dict)  # eşlenmemiş motor nöron tipi → adet

    @property
    def dofs(self) -> list[str]:
        return sorted({d for m in self.muscles for d in m.torque})

    def summary(self) -> str:
        n = sum(len(m.mn) for m in self.muscles)
        return f"{len(self.muscles)} kas, {n} motor nöron eşlendi; eşlenmeyen {sum(self.unmapped.values())} ({len(self.unmapped)} tip)"


def load_geometry() -> dict:
    return json.loads(GEOMETRY_PATH.read_text())


def _leg_dof(leg: str, key: str) -> str:
    return {
        "coxa_yaw": f"c_thorax-{leg}_coxa-yaw",
        "coxa_pitch": f"c_thorax-{leg}_coxa-pitch",
        "coxa_roll": f"c_thorax-{leg}_coxa-roll",
        "trochanter_pitch": f"{leg}_coxa-{leg}_trochanterfemur-pitch",
        "trochanter_roll": f"{leg}_coxa-{leg}_trochanterfemur-roll",
        "tibia_pitch": f"{leg}_trochanterfemur-{leg}_tibia-pitch",
        "tarsus_pitch": f"{leg}_tibia-{leg}_tarsus1-pitch",
    }[key]


def build_table(conn: Connectome, passive_stiffness: dict[str, float], geom: dict | None = None) -> MuscleTable:
    """Konnektomdaki motor nöronları gövde kaslarına bağlar.

    passive_stiffness: bölge → eklem sertliği (µN·mm/rad); en büyük torku
    açı aralığından hesaplamak için ("leg", "other").
    """
    geom = geom or load_geometry()
    nn = conn.neurons
    col = lambda c, empty="": nn[c].fillna(empty).astype(str).to_numpy(dtype=object)  # noqa: E731
    t = col("type", "(tipsiz)")
    sub = col("subclass")
    side = col("side")
    motor = np.isin(col("superclass"), ["vnc_motor", "cb_motor"])
    used = np.zeros(conn.n, dtype=bool)
    muscles: list[Muscle] = []
    k_leg, k_other = passive_stiffness["leg"], passive_stiffness["other"]
    nmf = geom["nmf"]

    def pick(mask):
        idx = np.flatnonzero(mask & motor)
        used[idx] = True
        return idx

    # Bacaklar: her bacak için ayrı kaslar (sol ön bacağın geometrisi, bacakların yapısal
    # benzerliği varsayımıyla tüm bacaklara uygulanır).
    leg_muscles = geom["muscles"]
    for sc, pos in LEG_SUBCLASS.items():
        for s in ("L", "R"):
            leg = s.lower() + pos
            by_muscle: dict[str, list[np.ndarray]] = {}
            for mn_type, names in LEG_MN_TO_MUSCLES.items():
                idx = pick((t == mn_type) & (sub == sc) & (side == s))
                for name in names:
                    by_muscle.setdefault(name, []).append(idx)
            for name, parts in by_muscle.items():
                idx = np.unique(np.concatenate(parts))
                if len(idx) == 0:
                    continue
                m = leg_muscles[name]
                # Kasılma tendonu kısaltır: tork = −kol × kuvvet.
                torque = {_leg_dof(leg, k): -v * m["F0_uN"] for k, v in m["arm_mm_per_rad"].items() if v != 0}
                muscles.append(Muscle(f"{leg}:{name}", idx, torque))
            sgn = nmf["legs"][leg]["tarsus_depression_sign"]
            for direction, label in ((+1, "tarsus_depressor"), (-1, "tarsus_levator")):
                types = [k for k, v in TARSUS_MN.items() if v == direction]
                idx = pick(np.isin(t, types) & (sub == sc) & (side == s))
                if len(idx):
                    tau = k_leg * RANGE_RAD["tarsus"] * direction * sgn
                    muscles.append(Muscle(f"{leg}:{label}", idx, {_leg_dof(leg, "tarsus_pitch"): tau}))

    # Sıçrama kası: orta bacak trokanter açıcısı, ölçülmüş uç kuvvetinden.
    ttm = geom["nmf"]["ttm"]
    ext_sign = 1 if leg_muscles["sterno-tergo-trochanter_extensor_a"]["arm_mm_per_rad"]["trochanter_pitch"] < 0 else -1
    for s in ("L", "R"):
        leg = s.lower() + "m"
        idx = pick((t == "TTMn") & (side == s))
        if len(idx):
            muscles.append(Muscle(f"{leg}:TTM", idx,
                                  {_leg_dof(leg, "trochanter_pitch"): ext_sign * ttm["torque_uNmm"]},
                                  gain=TWITCH_GAIN_TTM))

    # Hortum.
    joint = {"rostrum": nmf["rostrum_protraction"], "haustellum": nmf["haustellum_extension"]}
    for mn_type, effects in PROBOSCIS_MN.items():
        idx = pick(t == mn_type)
        if len(idx) == 0:
            continue
        torque = {joint[j]["dof"]: d * joint[j]["sign"] * k_other * RANGE_RAD[j] for j, d in effects.items()}
        muscles.append(Muscle(f"hortum:{mn_type}", idx, torque))

    # Boyun: VARSAYIM — her taraftaki boyun motor nöronları başı kendi tarafına çevirir.
    head = nmf["head_turn_left"]
    for s, d in (("L", +1), ("R", -1)):
        idx = pick((sub == "nm") & (side == s))
        if len(idx):
            muscles.append(Muscle(f"boyun:{s}", idx, {head["dof"]: d * head["sign"] * k_other * RANGE_RAD["head"]}))

    # Kanatlar.
    for s in ("L", "R"):
        w = nmf[f"{s.lower()}_wing_extension"]
        for types, d, label in ((WING_EXTEND, +1, "acma"), (WING_FOLD, -1, "katlama")):
            idx = pick(np.isin(t, types) & (side == s))
            if len(idx):
                muscles.append(Muscle(f"kanat:{s}:{label}", idx, {w["dof"]: d * w["sign"] * k_other * RANGE_RAD["wing"]}))

    # Karın: VARSAYIM — karın motor nöronları segmentleri aşağı büker; iki taraf
    # arasındaki fark yana bükülme üretir.
    for s, d in (("L", +1), ("R", -1)):
        idx = pick((sub == "ad") & (side == s))
        if len(idx) == 0:
            continue
        torque = {}
        for f in nmf["abdomen_ventral_flexion"]:
            torque[f["dof"]] = f["sign"] * k_other * RANGE_RAD["abdomen"]
        for f in nmf["abdomen_bend_left"]:
            torque[f["dof"]] = d * f["sign"] * k_other * RANGE_RAD["abdomen"]
        muscles.append(Muscle(f"karin:{s}", idx, torque))

    rest = np.flatnonzero(motor & ~used)
    unmapped = {}
    for i in rest:
        unmapped[t[i]] = unmapped.get(t[i], 0) + 1
    return MuscleTable(muscles, dict(sorted(unmapped.items())))


class MuscleModel:
    """Spike sayılarını eklem torklarına çeviren durumlu kas modeli."""

    def __init__(self, table: MuscleTable, dofs: list[str], ranges=None):
        self.table = table
        self.dofs = list(dofs)
        dof_idx = {d: i for i, d in enumerate(self.dofs)}
        self.mn = np.unique(np.concatenate([m.mn for m in table.muscles]))
        pos = {int(n): i for i, n in enumerate(self.mn)}
        n_mn, n_mus = len(self.mn), len(table.muscles)
        # Kas × motor nöron ortalama matrisi ve kas × eklem tork matrisi.
        self.avg = np.zeros((n_mus, n_mn))
        self.G = np.zeros((len(self.dofs), n_mus))
        self.gain = np.full(n_mn, TWITCH_GAIN)
        for k, m in enumerate(table.muscles):
            cols = [pos[int(i)] for i in m.mn]
            self.avg[k, cols] = 1.0 / len(cols)
            self.gain[cols] = np.maximum(self.gain[cols], m.gain)
            for d, tau in m.torque.items():
                if d not in dof_idx:
                    raise KeyError(f"{m.name}: gövdede {d} serbestlik derecesi yok")
                self.G[dof_idx[d], k] += tau
        self.Gp = np.maximum(self.G, 0.0)
        self.Gn = np.minimum(self.G, 0.0)
        if ranges is None:
            lo = hi = np.zeros(len(self.dofs))
            limited = np.zeros(len(self.dofs), dtype=bool)
        else:
            lo, hi, limited = ranges
        self.lo, self.hi, self.limited = lo, hi, limited
        self.width = np.where(limited, FL_MARGIN * (hi - lo), 1.0)
        self.reset()

    def reset(self):
        self.x = np.zeros(len(self.mn))
        self.force = np.zeros(self.avg.shape[0])

    def step(self, spikes: np.ndarray, dt_ms: float, angles: np.ndarray | None = None) -> np.ndarray:
        """spikes: bu adımda her motor nöronun (self.mn sırası) spike sayısı.
        angles: eklem açıları (dofs sırası); boy–kuvvet sınırı için. Tork döndürür."""
        self.x *= np.exp(-dt_ms / RELAX_MS)
        for _ in range(int(spikes.max(initial=0))):
            hit = spikes > 0
            self.x[hit] += self.gain[hit] * (1.0 - self.x[hit])
            spikes = spikes - hit
        activation = self.avg @ self.x
        self.force += (activation - self.force) * (1.0 - np.exp(-dt_ms / RISE_MS))
        if angles is None:
            return self.G @ self.force
        up = np.where(self.limited, np.clip((self.hi - angles) / self.width, 0.0, 1.0), 1.0)
        down = np.where(self.limited, np.clip((angles - self.lo) / self.width, 0.0, 1.0), 1.0)
        return up * (self.Gp @ self.force) + down * (self.Gn @ self.force)

    @property
    def activation(self) -> np.ndarray:
        return self.avg @ self.x
