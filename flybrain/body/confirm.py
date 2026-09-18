"""Gövde onayı (K-032): bir Instagram kararı, ilgili gövde bölgesi o pencerede görünür
biçimde hareket ettiyse uygulanır ("hareket yoksa eylem yok").

Kanal ve gövde ölçüsü eşlemesi:

| kanal  | eylem            | ölçü                                   | görünür         |
|--------|------------------|----------------------------------------|-----------------|
| ileri  | sonraki post     | bacak eklemlerinin açı yolu            | ≥ VISIBLE_DEG   |
| geri   | önceki post      | göğsün geriye yer değiştirmesi         | ≥ VISIBLE_MM    |
| hortum | beğen / kaydet   | hortum eklemlerinin açı yolu           | ≥ VISIBLE_DEG   |
| yorum  | yorum            | kanat eklemlerinin açı yolu            | ≥ VISIBLE_DEG   |
| takip  | takip et         | karın eklemlerinin açı yolu            | ≥ VISIBLE_DEG   |
| cikis  | çıkış            | göğsün en büyük yükselmesi (sıçrama)   | ≥ VISIBLE_MM    |
|        |                  | **bağlı sinekte:** TTM ekleminin yolu  | ≥ ESCAPE_DEG    |
| sekme  | sekme değiştir   | baş eklemlerinin açı yolu              | ≥ VISIBLE_DEG   |
| timar  | tımar            | ön bacak eklemlerinin açı yolu         | ≥ VISIBLE_DEG   |

Açı yolu: pencere boyunca 5 ms'lik örneklerde eklem açısı değişimlerinin mutlak toplamı,
bölgedeki eklemlerin ortalaması. Eşikler VARSAYIM: bir izleyicinin videoda fark
edebileceği en küçük hareket olarak seçildi.

Sıçrama: sinek o pencerede sıçradıysa gövdede görünen davranış kaçıştır; yalnızca çıkış
onaylanır. Sıçrama bütün gövdeyi savurur ve baş, karın, kanat eklemlerini de oynatır; ilk
doğrulamada sekme kararlarının hepsi sıçramalardaydı. Bağlı sinekte (K-040) "sıçrama" göğsün
yükselmesi değil sıçrama **hareketi**: gövde gidemez ama TTM eklemi aynı işi yapar ve çevresini
aynı şekilde savurur, bu yüzden dışlama kuralı aynen geçerli.

Sınır: Onay, bölgenin hareket ettiğini gösterir; hareketin kararı veren nöronlardan
geldiğini değil.
"""

import numpy as np

from flybrain.motor.readout import CHANNELS

REGIONS = {
    "bacak": ("lf_", "lm_", "lh_", "rf_", "rm_", "rh_"),
    "on_bacak": ("lf_", "rf_"),
    "hortum": ("rostrum", "haustellum"),
    "kanat": ("_wing",),
    "karin": ("abdomen",),
    "bas": ("c_thorax-c_head",),
    # Sıçrama kasının (TTM) kendi eklemleri: orta bacakların trokanter açıcısı. Dev lif →
    # TTMn → bu iki eklem (body/muscles.py). Bağlı sinekte kaçışın gövdedeki izi burada:
    # göğüs gidemez ama sıçrama hareketi bacaklarda tam olarak yapılır.
    "ttm": ("lm_coxa-lm_trochanterfemur-pitch", "rm_coxa-rm_trochanterfemur-pitch"),
}
MEASURES = tuple(REGIONS) + ("gogus_mm", "gogus_ileri_mm", "gogus_yukselme_mm", "gogus_savrulma_mm")
CHANNEL_MEASURE = {
    "ileri": "bacak",
    "geri": "gogus_ileri_mm",
    "hortum": "hortum",
    "yorum": "kanat",
    "takip": "karin",
    "cikis": "gogus_yukselme_mm",
    "sekme": "bas",
    "timar": "on_bacak",
}
VISIBLE_DEG = 1.0
VISIBLE_MM = 0.1

# Kaçışın gövdedeki karşılığı, sineğin serbest mi bağlı mı olduğuna göre değişir (K-040):
#
#   serbest : sıçrama, yani göğsün yükselmesi (≥ VISIBLE_MM).
#   bağlı   : sıçrama **hareketi**, yani TTM'nin kendi ekleminin açı yolu (≥ ESCAPE_DEG).
#             Bağlı sinekte göğüs hiçbir şey söylemiyor: dev lifin ateşlediği pencerelerde bile
#             yükselme 0,003 mm, savrulma 0,005 mm — ikisi de eşiğin çok altında ve dinlenmeden
#             ayrışmıyor. Bağı gevşetmek çözmüyor (10/20/40/80 ms tarandı): kaçış savrulmasını
#             artırmıyor, yalnızca dinlenmedeki salınımı büyütüyor.
#
# ESCAPE_DEG **serbest** sinekten çıkarıldı, bağlı sinekten değil: sineğin gerçekten sıçradığı
# pencerelerde (göğüs ≥ VISIBLE_MM yükselmiş) TTM ekleminin açı yolu ölçüldü. Böylece eşik
# "kaçış hareketi neye benzer" sorusunun serbest sinekteki cevabı; dev lif spike'larından
# türetilmedi (yoksa gövde onayı nöronun kendisini tekrar okumuş olurdu, K-032'nin amacına ters).
#
#   TTM eşiği | serbest sıçrama | serbest sakin | bağlı dev lif | bağlı sakin
#      10°    |      %100       |      %16      |     %100      |     %3
#      20°    |      %100       |       %0      |     %100      |     %2    ← seçilen
#      40°    |       %91       |       %0      |      %75      |     %1
#
# Ölçüm: flybrain/experiments/bag.py (docs/09-govde.md 18).
ESCAPE_MEASURE = "gogus_yukselme_mm"
TETHERED_ESCAPE_MEASURE = "ttm"
ESCAPE_DEG = 20.0


def _heading(quat: np.ndarray) -> np.ndarray:
    """Göğsün ileri ekseninin yatay bileşeni (birim vektör)."""
    w, x, y, z = quat
    v = np.array([1 - 2 * (y * y + z * z), 2 * (x * y + w * z)])
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.array([1.0, 0.0])


class BodyMeter:
    def __init__(self, dofs: list[str]):
        self.masks = {k: np.array([any(p in d for p in pats) for d in dofs]) for k, pats in REGIONS.items()}

    def measure(self, arrays: dict[str, np.ndarray]) -> np.ndarray:
        """Bir pencerenin kaydından (Trace.arrays()) MEASURES sırasıyla ölçüler."""
        path = np.abs(np.diff(arrays["angles"], axis=0)).sum(axis=0)
        th = arrays["thorax"]
        step = th[-1, :2] - th[0, :2]
        return np.array([path[m].mean() if m.any() else 0.0 for m in self.masks.values()] + [
            float(np.linalg.norm(step)),
            float(step @ _heading(arrays["thorax_quat"][0])),
            float(th[:, 2].max() - th[0, 2]),
            float(np.linalg.norm(th - th[0], axis=1).max()),
        ])


def visible(measures: np.ndarray, tethered: bool = False) -> np.ndarray:
    """[..., MEASURES] ölçülerden [..., CHANNELS] görünür hareket (bool).

    tethered: sinek bağlıysa kaçışın ölçüsü TTM ekleminin açı yoludur (K-040).
    """
    escape = TETHERED_ESCAPE_MEASURE if tethered else ESCAPE_MEASURE
    limit = np.radians(ESCAPE_DEG) if tethered else VISIBLE_MM
    jumped = measures[..., MEASURES.index(escape)] >= limit
    out = []
    for c in CHANNELS:
        key = CHANNEL_MEASURE[c]
        m = measures[..., MEASURES.index(key)]
        if c == "cikis":
            out.append(jumped)
        elif key.startswith("gogus"):
            out.append(((-m if c == "geri" else m) >= VISIBLE_MM) & ~jumped)
        else:
            out.append((m >= np.radians(VISIBLE_DEG)) & ~jumped)
    return np.stack(out, axis=-1)
