"""Görme kodlayıcısı: görsel → göz kolonları → görme nöronlarının uyarımı.

Fotoreseptörler histaminerjik (ketleyici) olduğu için sessiz bir LIF modelinde
doğrudan uyarılmaları aşağı akışta hiçbir şey üretmez (Z-02). Üç yöntem var:

- "off":   karanlık bölgeler, OFF yolunun ilk uyarıcı nöronlarını (L2, L3) sürer.
- "onoff": "off" + parlak bölgeler, ON yolunun uyarıcı nöronlarını (Mi1, Tm3) sürer.
           Gerçek sinekte bu nöronlar L1 üzerinden işaret dönüşümüyle ışığa yanıt verir.
- "foto":  ışık fotoreseptörleri sürer (R1–R6 parlaklık, R7/R8 renk). Lamina
           nöronları (L1–L3) ve ON yolu nöronları (Mi1, Tm3), ışıkta sürekli aktif
           olmalarını taklit eden tonik akım alır; fotoreseptörler onları ketler.

Görsel, sinek gözü gibi kontrast olarak kodlanır: c = (I − Ī) / Ī. Ī görselin
ortalama parlaklığıdır. Gri ekran sıfır kontrast, yani "off" ve "onoff"
yöntemlerinde sıfır uyarım demektir.

Sinekler kırmızıyı neredeyse göremez. Parlaklık kanalı buna göre tartılır
(LUM_WEIGHTS); R7 (UV) için mavi kanal vekil olarak kullanılır.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from flybrain.anatomy import SENSORY, pools
from flybrain.connectome.connectome import Connectome
from flybrain.senses.eye import Eye
from flybrain.sim.stimulus import Stimulus

LUM_WEIGHTS = np.array([0.05, 0.55, 0.40])  # R, G, B
ACCEPTANCE_DEG = 5.0      # ommatidyum kabul açısı (yarı yükseklikte tam genişlik)
CONTRAST_SAT = 0.6        # bu kontrasttan sonra yanıt doyar
MODES = ("off", "onoff", "foto")


@dataclass(frozen=True)
class VisionConfig:
    mode: str = "onoff"
    r_max_hz: float = 50.0          # doymuş kontrasttaki hız
    r_base_hz: float = 50.0         # "foto": ortalama parlaklıkta fotoreseptör hızı
    tonic_mv: float = 9.0           # "foto": tonik akım (eşik farkı 7 mV)


def load_image(path: str | Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0


def _channels(img: np.ndarray) -> dict[str, np.ndarray]:
    img = np.asarray(img, dtype=np.float64)
    if img.ndim == 2:
        img = np.repeat(img[..., None], 3, axis=2)
    return {
        "lum": img @ LUM_WEIGHTS,
        "green": img[..., 1],
        "blue": img[..., 2],
    }


def neuron_groups(conn: Connectome, mode: str) -> tuple[list[tuple[str, np.ndarray, str, int, str]], list[np.ndarray]]:
    """Yönteme göre sürülen nöron grupları ve tonik akım alan nöronlar.

    Grup: (ad, nöronlar, kanal, kutup, dinamik); kutup +1 aydınlığa, −1 karanlığa yanıt.
    Dinamik yalnızca zamanla değişen sahnede kullanılır (body/sight.py): L1/L2, Mi1 ve Tm3
    geçici (çift fazlı), L3 ve fotoreseptörler kalıcı yanıt verir (Yang ve Clandinin 2018 derlemesi;
    Arenz ve ark. 2017).
    """
    if mode not in MODES:
        raise ValueError(f"bilinmeyen yöntem: {mode}")
    S = pools(conn, SENSORY)
    sel = conn.select
    groups: list[tuple[str, np.ndarray, str, int, str]] = []
    tonic: list[np.ndarray] = []
    if mode in ("off", "onoff"):
        groups += [
            ("L2", sel(type="L2"), "lum", -1, "gecici"),
            ("L3", sel(type="L3"), "lum", -1, "kalici"),
        ]
    if mode == "onoff":
        groups += [
            ("Mi1", sel(type="Mi1"), "lum", +1, "gecici"),
            ("Tm3", sel(type="Tm3"), "lum", +1, "gecici"),
        ]
    if mode == "foto":
        groups += [
            ("R1-R6", S["R1_R6"], "lum", +1, "kalici"),
            ("R7", S["R7"], "blue", +1, "kalici"),
            ("R8p", sel(type="R8p"), "blue", +1, "kalici"),
            ("R8y", sel(type=["R8y", "R8d", "R8_unclear"]), "green", +1, "kalici"),
        ]
        tonic = [sel(type=["L1", "L2", "L3", "Mi1", "Tm3"])]
    return groups, tonic


def contrast_to_stimulus(cfg: VisionConfig, groups: list[tuple[str, np.ndarray, int]],
                         contrast: dict[str, np.ndarray]) -> Stimulus:
    """Grup başına kolon kontrastını Poisson hızlarına çevirir. groups: (ad, nöronlar, kutup)."""
    stim = Stimulus.empty()
    for name, idx, polarity in groups:
        c = contrast[name] * polarity
        if cfg.mode == "foto":
            hz = cfg.r_base_hz * np.clip(1.0 + c, 0.0, 1.0 + CONTRAST_SAT)
        else:
            hz = cfg.r_max_hz * np.clip(c / CONTRAST_SAT, 0.0, 1.0)
        stim = stim + Stimulus.of(idx, hz)
    return stim


class VisionEncoder:
    def __init__(self, conn: Connectome, config: VisionConfig = VisionConfig(), eye: Eye | None = None):
        self.conn = conn
        self.cfg = config
        self.eye = eye or Eye(conn)
        groups, tonic = neuron_groups(conn, config.mode)

        self.groups = []
        for name, idx, channel, polarity, _ in groups:
            kept, u, v = self.eye.neuron_uv(idx)
            self.groups.append((name, kept, u, v, channel, polarity))

        self.bias_mv = None
        if tonic:
            self.bias_mv = np.zeros(conn.n)
            self.bias_mv[np.concatenate(tonic)] = config.tonic_mv

        # Kodlayıcının doğrudan sürdüğü nöronlar: sinaptik depresyondan muaf tutulur.
        self.input_neurons = np.unique(np.concatenate([g[1] for g in self.groups] + tonic))

    def coverage(self) -> dict[str, int]:
        return {name: len(idx) for name, idx, *_ in self.groups}

    def column_contrast(self, img: np.ndarray) -> dict[str, np.ndarray]:
        """Her grubun nöronları için kanal kontrastı."""
        chans = _channels(img)
        h, w = chans["lum"].shape
        span = self.eye.phi_range[1] - self.eye.phi_range[0]
        sigma = w * (ACCEPTANCE_DEG / 2.355) / (2 * span)  # görsel genişliği iki gözün toplam açısı
        out = {}
        for name, _, u, v, channel, _ in self.groups:
            ch = chans[channel]
            mean = ch.mean()
            blurred = gaussian_filter(ch, sigma)
            vals = map_coordinates(blurred, [v * (h - 1), u * (w - 1)], order=1, mode="nearest")
            out[name] = (vals - mean) / max(mean, 1e-3)
        return out

    def encode(self, img: np.ndarray) -> Stimulus:
        groups = [(name, idx, polarity) for name, idx, _, _, _, polarity in self.groups]
        return contrast_to_stimulus(self.cfg, groups, self.column_contrast(img))

    def gray(self) -> Stimulus:
        """Gri ekran: "foto" yönteminde fotoreseptörlerin taban hızı, diğerlerinde boş."""
        return self.encode(np.full((8, 8, 3), 0.5))
