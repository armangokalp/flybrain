"""Motor okuma: çıkış nöronlarının spike sayılarından davranış kanallarına (K-015).

Faz 4 ölçümlerinde tek tük komut nöronlarının (DNp09, oDN1, P1, MN11/12...)
gerçekçi postlarda neredeyse hiç ateşlemediği görüldü. Bu yüzden okuma,
motor nöronların sürdüğü vücut bölgesine (MaleCNS `subclass` anotasyonu) göre
gruplanmış kas kanallarından yapılır:

| kanal  | davranış                     | nöronlar                                           |
|--------|------------------------------|----------------------------------------------------|
| ileri  | yürüme                       | ön, orta, arka bacak motor nöronları (fl, ml, hl)  |
| geri   | geri yürüme                  | MDN komut nöronları                                |
| hortum | hortum hareketleri (besleme) | beyin hortum motor nöronları (pm)                  |
| yorum  | kanat titreşimi (kur şarkısı)| kanat yönlendirme motor nöronları (wm; DLM/DVM ve sıçrama kasları TTMn/STTMm hariç) |
| takip  | karın bükme (çiftleşme girişimi) | karın motor nöronları (ad)                     |
| cikis  | kaçış / havalanma            | alt tectulum'a inen nöronlar (lt; Giant Fiber dahil) |
| sekme  | baş çevirme                  | boyun motor nöronlarında sol−sağ farkı (nm)        |
| timar  | ön bacakla temizlenme        | ön bacak MN hızı − orta/arka bacak MN hızı         |

Her kanal nöron başına ortalama hız (Hz) olarak hesaplanır. Sekme kanalı, sol ve
sağ boyun nöronlarının toplam spike farkının mutlak değeridir; birikimli spike
sayılarıyla çağrıldığında birikimli farkı verir.

Sıçrama kaslarının motor nöronları (TTMn, STTMm) MaleCNS'te kanat alt sınıfında; ama
kanadı değil orta bacağı çalıştırıp sıçrama üretiyorlar (docs/09-govde.md). Bu yüzden
yorum kanalından çıkarıldılar (2026-09-17, Z-27); sıçramayı çıkış kanalı dev lif
üzerinden zaten okuyor.
"""

import re

import numpy as np

from flybrain.anatomy import MOTOR, pools
from flybrain.connectome.connectome import Connectome

CHANNELS = ("ileri", "geri", "hortum", "yorum", "takip", "cikis", "sekme", "timar")


class MotorReadout:
    def __init__(self, conn: Connectome):
        sel = conn.select
        wing = sel(superclass="vnc_motor", subclass="wm")
        power = sel(superclass="vnc_motor", subclass="wm", type=re.compile(r"^(?:DLMn|DVMn|TTMn|STTMm)"))
        self.groups = {
            "ileri": sel(superclass="vnc_motor", subclass=["fl", "ml", "hl"]),
            "geri": pools(conn, MOTOR)["geri_yuru"],
            "hortum": sel(superclass="cb_motor", subclass="pm"),
            "yorum": np.setdiff1d(wing, power),
            "takip": sel(superclass="vnc_motor", subclass="ad"),
            "cikis": sel(superclass="descending_neuron", subclass="lt"),
        }
        neck = np.union1d(sel(superclass="vnc_motor", subclass="nm"), sel(superclass="cb_motor", subclass="nm"))
        side = conn.neurons.side.to_numpy()
        self.neck_left = neck[side[neck] == "L"]
        self.neck_right = neck[side[neck] == "R"]
        self.front_legs = sel(superclass="vnc_motor", subclass="fl")
        self.other_legs = sel(superclass="vnc_motor", subclass=["ml", "hl"])

    def sizes(self) -> dict[str, int]:
        out = {k: len(v) for k, v in self.groups.items()}
        out["sekme"] = len(self.neck_left) + len(self.neck_right)
        out["timar"] = len(self.front_legs)
        return out

    def single_spike_rates(self, duration_ms: float) -> np.ndarray:
        """Her kanalda tek bir spike'ın yarattığı hız (sayma gürültüsü tabanı)."""
        sec = duration_ms / 1000.0
        n = self.sizes()
        return np.array([1.0 / (n[k] * sec) for k in CHANNELS])

    def rates(self, counts: np.ndarray, duration_ms: float) -> tuple[np.ndarray, float]:
        """(kanal hızları CHANNELS sırasıyla, baş çevirme yönü: + sol, − sağ)."""
        sec = duration_ms / 1000.0

        def hz(ix):
            return counts[ix].sum() / len(ix) / sec

        neck_diff = (counts[self.neck_left].sum() - counts[self.neck_right].sum()) / (
            (len(self.neck_left) + len(self.neck_right)) * sec
        )
        values = {k: hz(v) for k, v in self.groups.items()}
        values["sekme"] = abs(neck_diff)
        values["timar"] = hz(self.front_legs) - hz(self.other_legs)
        return np.array([values[k] for k in CHANNELS]), float(np.sign(neck_diff))
