"""Duygu okuması: "beynin neresi yanıyor" (K-036).

Motor okuması (`motor/readout.py`) sineğin **ne yaptığını** okur; bu modül **hangi devrenin
etkin olduğunu** okur. Yöntem aynı: adlandırılmış nöron havuzlarının nöron başına ateşleme hızı.
Eğitilmiş yorumlayıcı yok; havuzlar anatomiye dayanıyor ve elle yazılmış.

| duygu | havuz | dayanak |
|---|---|---|
| korku | LC4 + LPLC2 (311), dev lif DNp01 (2) | yaklaşma/kararma algılayıcıları ve kaçış komutu |
| besleme | beyin hortum motor nöronları (67) | hortum uzatma; beğeni kanalıyla aynı havuz |
| kur | pC1 / P1 soyu (49) + şarkı komutu pIP10, vPR6 (10) | erkeğe özgü kur devresi (K-017) |
| ödül | PAM dopamin (316) | gelen beğeni, yeni takipçi (`senses/reward.py`) |
| ceza | PPL1 dopamin (16) | takipçi kaybı |
| rahatsızlık | aDN1, aDN2 tımar komutu (4) | ön bacakla temizlenme (Hampel ve ark. 2015) |

**Baskın duygu**, kalibrasyondaki ortalama ve standart sapmaya göre en yüksek z-skoru olan
havuzdur (motor kanallarındaki kuralın aynısı, sayma gürültüsü tabanıyla). Kalibrasyon içerikten
bağımsız referans postlarla yapılır: `python -m flybrain.experiments.mood_calibrate`.

**Bilinen sınır:** Modelde açlık gibi bir *dürtü* yok; "besleme" havuzu yalnızca o anki hortum
etkinliğini gösterir. Kur havuzu gerçekçi postlarda neredeyse hiç ateşlemiyor (K-017).
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from flybrain.connectome.connectome import Connectome

MOODS = ("korku", "besleme", "kur", "odul", "ceza", "rahatsizlik")
CALIBRATION_PATH = Path(__file__).with_name("mood_calibration.json")

# Duygu → emoji ve yorumun kelime sayısı. Bu tablo **insan tarafından** yazıldı; sinek yalnızca
# hangi duygunun baskın olduğunu seçer (K-036). Kelimeler sinekten gelir, bu satırlar değil.
MOOD_STYLE = {
    "korku":       {"emoji": "😨", "words": 1},
    "besleme":     {"emoji": "🍯", "words": 3},
    "kur":         {"emoji": "🪰", "words": 4},
    "odul":        {"emoji": "✨", "words": 3},
    "ceza":        {"emoji": "🌧", "words": 2},
    "rahatsizlik": {"emoji": "🧹", "words": 2},
}


def mood_pools(conn: Connectome) -> dict[str, np.ndarray]:
    sel = conn.select
    return {
        "korku": np.union1d(sel(type=["LC4", "LPLC2"]), sel(type="DNp01")),
        "besleme": sel(superclass="cb_motor", subclass="pm"),
        "kur": np.union1d(sel(type=re.compile(r"^pC1_"), fruDsx="coexpress_high"),
                          sel(type=["pIP10", "vPR6"])),
        "odul": sel(**{"class": "DAN"}, type=re.compile(r"^PAM")),
        "ceza": sel(**{"class": "DAN"}, type=re.compile(r"^PPL1")),
        "rahatsizlik": sel(type=["DNg62", "DNge078"]),
    }


@dataclass(frozen=True)
class MoodCalibration:
    """Referans postlardaki ortalama ve standart sapma (duygu sırası MOODS)."""

    mean: list[float]
    std: list[float]
    window_ms: float
    posts: int

    @classmethod
    def fit(cls, rates: np.ndarray, window_ms: float, floor: np.ndarray) -> "MoodCalibration":
        """rates: [post, duygu] hızlar. floor: sayma gürültüsü tabanı (tek spike'ın hızı)."""
        return cls(mean=rates.mean(0).tolist(),
                   std=np.maximum(rates.std(0), floor).tolist(),
                   window_ms=float(window_ms), posts=int(len(rates)))

    def save(self, path: Path | str = CALIBRATION_PATH) -> Path:
        path = Path(path)
        path.write_text(json.dumps({"duygular": list(MOODS), "ortalama": self.mean, "std": self.std,
                                    "pencere_ms": self.window_ms, "post": self.posts},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | str = CALIBRATION_PATH) -> "MoodCalibration":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        if tuple(d["duygular"]) != MOODS:
            raise ValueError(f"kalibrasyondaki duygular farklı: {d['duygular']}")
        return cls(d["ortalama"], d["std"], d["pencere_ms"], d["post"])


class MoodReadout:
    def __init__(self, conn: Connectome, calibration: MoodCalibration | None = None):
        self.groups = mood_pools(conn)
        for name, idx in self.groups.items():
            if len(idx) == 0:
                raise ValueError(f"boş duygu havuzu: {name}")
        self.cal = calibration

    def sizes(self) -> dict[str, int]:
        return {k: len(v) for k, v in self.groups.items()}

    def single_spike_rates(self, duration_ms: float) -> np.ndarray:
        sec = duration_ms / 1000.0
        return np.array([1.0 / (len(self.groups[m]) * sec) for m in MOODS])

    def rates(self, counts: np.ndarray, duration_ms: float) -> np.ndarray:
        """Havuz başına nöron başına ortalama hız (Hz), MOODS sırasıyla."""
        sec = duration_ms / 1000.0
        return np.array([counts[self.groups[m]].sum() / len(self.groups[m]) / sec for m in MOODS])

    def z(self, counts: np.ndarray, duration_ms: float) -> dict[str, float]:
        if self.cal is None:
            raise RuntimeError("duygu kalibrasyonu yok (experiments/mood_calibrate.py)")
        r = self.rates(counts, duration_ms)
        z = (r - np.array(self.cal.mean)) / np.array(self.cal.std)
        return {m: float(v) for m, v in zip(MOODS, z)}

    def dominant(self, counts: np.ndarray, duration_ms: float) -> tuple[str, dict[str, float]]:
        """(baskın duygu, bütün z-skorları)."""
        z = self.z(counts, duration_ms)
        return max(z, key=z.get), z
