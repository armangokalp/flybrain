"""Eylem seçimi: kanal hızları → Instagram eylemi (K-016, K-017, K-018).

Sinek bir posta 500 ms'lik pencerelerle bakar (en fazla MAX_WINDOWS pencere).
Kanıt birikimlidir: w. pencerenin sonunda kanal hızları, posta bakmaya
başlandığından beri biriken spike'lardan hesaplanır ve referans postlardan
çıkarılmış (aynı birikim süresine ait) ortalama ve standart sapmayla z-skora
çevrilir. Bu z-skor, "bu post, sineğin tipik bir posta verdiği yanıta göre hangi
kası olağandışı çalıştırıyor?" sorusunun cevabıdır.

Eşikler eylem bütçesinden gelir (K-016). Karar kuralı referans postlarda bütünüyle
uygulanır ve her kanalın eşiği, o kanalın eyleminin GERÇEKLEŞEN oranı
BUDGET[kanal] olana kadar ayarlanır (kanallar arası yarış hesaba katılır).
Böylece genel sıklıkları insan belirler, hangi postta ne yapılacağını sinek seçer.

Karar kuralı:
  0. Hızı sıfır ya da negatif olan kanal karar veremez (spike yoksa eylem yok). Neredeyse hiç
     ateşlemeyen kanallarda z-skoru eşiği spike olmadan da aşabiliyordu (gövdeli sinekte
     geri kanalı, docs/09-govde.md 17). Gövdeli sinekte ayrıca ilgili gövde bölgesi o
     pencerede görünür biçimde hareket etmiş olmalı (gövde onayı, K-032, body/confirm.py).
  1. Eşiğini aşan kanallar arasından, eşiği en büyük farkla aşan seçilir.
  2. Hiçbiri aşmıyorsa sinek bakmaya devam eder (bir pencere daha).
  3. MAX_WINDOWS sonunda hâlâ karar yoksa sinek "ilgisini kaybeder" ve kaydırır.

Sayma gürültüsü tabanı: her kanalın standart sapması, o birikim süresinde tek bir
spike'ın yarattığı hızdan küçük kabul edilmez (Calibration.fit, `floor`).

Eşik homeostazı (K-016 eki): kullanımda eşikler her karardan sonra çok az kaydırılır;
bir eylem bütçesinden sık seçiliyorsa eşiği yükselir, seyrek seçiliyorsa düşer
(Robbins-Monro). Kaydetme eşiğinin ayrı denetleyicisi yalnızca hortum kararlarında
çalışır ve bu kararlar içindeki kaydetme payını SAVE_SHARE'e çeker. Bu mekanizma
yalnızca genel sıklığı bütçeye yaklaştırır; hangi postun daha güçlü yanıt aldığı
sıralaması tamamen sinekte kalır. Gerekçe: kalibrasyon postları
ile gerçek feed arasındaki fark ve erken kararların beyin geçmişini değiştirmesi,
sabit eşiklerin gerçekleşen oranlarını kaydırıyor (docs/08-motor.md).

Hortum kanalında iki şiddet düzeyi var (K-018):
  - orta şiddet (z ≥ θ_beğen)  → beğen
  - yüksek şiddet (z ≥ θ_kaydet) → kaydet
  θ_kaydet, referans postlardaki hortum kararlarının EN FAZLA
  SAVE_BUDGET / BUDGET["hortum"] kadarının (yaklaşık %13) kaydetme olacağı en küçük
  değerdir ve θ_beğen'in en az SAVE_MIN_GAP standart sapma üstünde olmak zorundadır.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from flybrain.motor.readout import CHANNELS

WINDOW_MS = 500
MAX_WINDOWS = 3
SCROLL_GAP_MS = 300  # postlar arası kaydırma sırasında gri ekran

# Bir postta o kanalın eyleminin seçilme hedefi (kanallar yarıştığı için gerçekleşen
# oran biraz daha düşük olur). Kalan postlarda sinek ilgisini kaybedip kaydırır.
BUDGET = {
    "ileri": 0.35,
    "geri": 0.03,
    "hortum": 0.15,   # beğen + kaydet
    "yorum": 0.02,
    "takip": 0.02,
    "cikis": 0.02,
    "sekme": 0.05,
    "timar": 0.05,
}
SAVE_BUDGET = 0.02
SAVE_MIN_GAP = 1.0
HOMEOSTASIS_RATE = 0.05       # karar başına eşik adımı (z birimi)
SAVE_HOMEOSTASIS_RATE = 0.15  # hortum kararı başına kaydetme eşiği adımı
SAVE_SHARE = SAVE_BUDGET / BUDGET["hortum"]  # hortum kararları içinde kaydetme payı hedefi (~%13)

CALIBRATION_PATH = Path(__file__).with_name("calibration.json")
# Gövdeli sineğin kalibrasyonu (experiments/embodied_calibrate.py, K-032).
CALIBRATION_EMBODIED_PATH = Path(__file__).with_name("calibration_embodied.json")
# Bağlı sineğin kalibrasyonu (K-040). Bağlı sinekte propriyosepsiyon ve görme farklı çalışıyor
# (gövde hareket edemiyor), yani kanalların tipik düzeyi de farklı; eşikler ayrı çıkarılır.
CALIBRATION_TETHERED_PATH = Path(__file__).with_name("calibration_tethered.json")


@dataclass
class Calibration:
    channels: list[str]
    mean: list[list[float]]   # [pencere][kanal]
    std: list[list[float]]
    theta: dict[str, float]
    save_theta: float
    budget: dict[str, float]
    save_budget: float
    n_posts: int
    disabled: list[str] = field(default_factory=list)  # referansta hiç değişmeyen kanallar
    raw_std: list[list[float]] = field(default_factory=list)  # tabansız standart sapma (rapor için)
    realized: dict[str, float] = field(default_factory=dict)  # referansta gerçekleşen eylem oranları
    body_confirmation: bool = False  # eşikler gövde onayıyla mı çıkarıldı (K-032)

    def save(self, path: Path = CALIBRATION_PATH) -> None:
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n")

    @staticmethod
    def load(path: Path = CALIBRATION_PATH) -> "Calibration":
        return Calibration(**json.loads(path.read_text()))

    @staticmethod
    def fit(cum_rates: np.ndarray, floor: np.ndarray, visible: np.ndarray | None = None) -> "Calibration":
        """cum_rates: [post, pencere, kanal] birikimli referans hızları.
        floor: [pencere, kanal] tek spike'ın o birikim süresinde yarattığı hız.
        visible: [post, pencere, kanal] gövde onayı (K-032); verilirse karar kuralı bununla uygulanır.
        """
        mean = cum_rates.mean(axis=0)
        raw_std = cum_rates.std(axis=0)
        disabled = [c for j, c in enumerate(CHANNELS) if (raw_std[:, j] == 0).all()]
        std = np.maximum(raw_std, floor)
        Z = (cum_rates - mean) / std
        active = cum_rates > 0
        if visible is not None:
            active &= visible
        enabled = np.array([c not in disabled for c in CHANNELS])
        target = np.array([BUDGET[c] for c in CHANNELS])

        peak = Z.max(axis=1)
        theta = np.array([np.quantile(peak[:, j], 1 - target[j]) for j in range(len(CHANNELS))])
        for _ in range(12):  # kanal kanal ikiye bölme; yarış yüzünden birkaç tur
            for j in np.flatnonzero(enabled):
                lo, hi = -10.0, 50.0
                for _ in range(40):
                    theta[j] = (lo + hi) / 2
                    rate = (_simulate(Z, theta, enabled, active)[1] == j).mean()
                    lo, hi = (theta[j], hi) if rate > target[j] else (lo, theta[j])
                theta[j] = (lo + hi) / 2

        first, winner, z_at = _simulate(Z, theta, enabled, active)
        h = CHANNELS.index("hortum")
        z_h = z_at[winner == h]
        share = SAVE_BUDGET / BUDGET["hortum"]
        # Muhafazakâr: hortum kararlarının en fazla `share` kadarı kaydetme olacak en küçük değer.
        # (Spike sayıları tam sayı olduğundan z-skorlarda eşit değerler çok; kantil tek başına yetmez.)
        candidates = [v for v in np.unique(z_h) if (z_h >= v).mean() <= share]
        save_q = float(candidates[0]) if candidates else float("inf")
        save_theta = max(save_q, float(theta[h]) + SAVE_MIN_GAP)

        realized = {c: float((winner == j).mean()) for j, c in enumerate(CHANNELS)}
        realized["kaydet"] = float(((winner == h) & (z_at >= save_theta)).mean())
        realized["ilgi_kaybi"] = float((winner < 0).mean())
        return Calibration(
            channels=list(CHANNELS),
            mean=mean.tolist(),
            std=std.tolist(),
            theta={c: float(t) for c, t in zip(CHANNELS, theta)},
            save_theta=save_theta,
            budget=dict(BUDGET),
            save_budget=SAVE_BUDGET,
            n_posts=int(cum_rates.shape[0]),
            disabled=disabled,
            raw_std=raw_std.tolist(),
            realized=realized,
            body_confirmation=visible is not None,
        )


def _simulate(Z: np.ndarray, theta: np.ndarray, enabled: np.ndarray, active: np.ndarray | None = None):
    """Karar kuralını [post, pencere, kanal] z-skorlarına uygular.

    active: [post, pencere, kanal] kanal hızı > 0 (verilmezse hepsi etkin sayılır).
    Döndürür: (karar penceresi, kazanan kanal, kazananın z-skoru); karar yoksa −1.
    """
    allowed = enabled if active is None else enabled & active
    over = np.where(allowed, Z - theta, -np.inf)
    best = over.max(axis=2)
    hit = best > 0
    decided = hit.any(axis=1)
    first = np.where(decided, hit.argmax(axis=1), -1)
    winner = np.full(len(Z), -1)
    z_at = np.full(len(Z), np.nan)
    rows = np.flatnonzero(decided)
    winner[rows] = over[rows, first[rows]].argmax(axis=1)
    z_at[rows] = Z[rows, first[rows], winner[rows]]
    return first, winner, z_at


@dataclass
class Decision:
    action: str          # ileri, geri, begen, kaydet, yorum, takip, cikis, sekme_sol, sekme_sag, timar, ilgi_kaybi
    channel: str | None  # kararı veren kanal; ilgi kaybında None
    window: int          # kararın verildiği pencere (0'dan başlar)
    dwell_ms: int        # posta bakma süresi
    z: dict[str, float]  # karar penceresindeki z-skorları
    reason: str
    body: dict[str, float] | None = None  # gövdeli sinekte karar penceresinin gövde ölçüleri
    bout: int = 0        # bağlı sinekte kaçıncı bakış nöbeti (K-040); serbest sinekte hep 0


ACTION_OF_CHANNEL = {
    "ileri": "ileri",
    "geri": "geri",
    "yorum": "yorum",
    "takip": "takip",
    "cikis": "cikis",
    "timar": "timar",
}


class ActionSelector:
    def __init__(self, calibration: Calibration, homeostasis: bool = True):
        self.cal = calibration
        self.mean = np.array(calibration.mean)
        self.std = np.array(calibration.std)
        self.theta = np.array([calibration.theta[c] for c in CHANNELS])
        self.save_theta = calibration.save_theta
        self.enabled = np.array([c not in calibration.disabled for c in CHANNELS])
        self.homeostasis = homeostasis
        self.target = np.array([calibration.budget[c] for c in CHANNELS])

    def state(self) -> dict:
        """Kaydedilip sonraki oturumda sürdürülebilecek eşikler."""
        return {"theta": dict(zip(CHANNELS, self.theta.tolist())), "save_theta": self.save_theta}

    def learn(self, decision: Decision) -> None:
        """Eşik homeostazı: gerçekleşen sıklığı bütçeye doğru iter."""
        if not self.homeostasis:
            return
        chosen = np.array([decision.channel == c for c in CHANNELS], dtype=float)
        self.theta += np.where(self.enabled, HOMEOSTASIS_RATE * (chosen - self.target), 0.0)
        if decision.channel == "hortum":
            saved = float(decision.action == "kaydet")
            self.save_theta += SAVE_HOMEOSTASIS_RATE * (saved - SAVE_SHARE)
        h = CHANNELS.index("hortum")
        self.save_theta = max(self.save_theta, self.theta[h] + SAVE_MIN_GAP)

    def zscores(self, window: int, rates: np.ndarray) -> np.ndarray:
        w = min(window, len(self.mean) - 1)
        return (rates - self.mean[w]) / self.std[w]

    def step(self, window: int, rates: np.ndarray, turn_sign: float,
             visible: np.ndarray | None = None) -> Decision | None:
        """visible: kanal başına gövde onayı (K-032); verilmezse onay aranmaz (gövdesiz sinek)."""
        z = self.zscores(window, rates)
        allowed = self.enabled & (rates > 0)
        if visible is not None:
            allowed &= visible
        over = np.where(allowed, z - self.theta, -np.inf)
        zdict = {c: round(float(v), 3) for c, v in zip(CHANNELS, z)}
        dwell = (window + 1) * WINDOW_MS
        if over.max() <= 0:
            if window + 1 >= MAX_WINDOWS:
                return Decision("ilgi_kaybi", None, window, dwell, zdict, "hiçbir kanal eşiği aşmadı")
            return None
        j = int(np.argmax(over))
        channel = CHANNELS[j]
        reason = f"{channel}: z={z[j]:.2f} > eşik {self.theta[j]:.2f}"
        if channel == "hortum":
            if z[j] >= self.save_theta:
                reason += f"; kaydetme eşiği {self.save_theta:.2f} de aşıldı"
                return Decision("kaydet", channel, window, dwell, zdict, reason)
            return Decision("begen", channel, window, dwell, zdict, reason)
        if channel == "sekme":
            action = "sekme_sol" if turn_sign > 0 else "sekme_sag"
            return Decision(action, channel, window, dwell, zdict, reason)
        return Decision(ACTION_OF_CHANNEL[channel], channel, window, dwell, zdict, reason)
