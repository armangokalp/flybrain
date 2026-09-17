"""Telefon ekranının görüntüsü: Instagram akışına benzeyen bir düzen (Faz 5 yer tutucusu).

Faz 8'de ekrana gerçek Instagram'ın ekran görüntüsü gelecek. O zamana kadar sahnede aynı
düzende bir yer tutucu çizilir; oranlar Instagram'ın dikey akışından alındı.

Ekran iki katmandan oluşur:
  - Sabit çerçeve: durum çubuğu ve başlık (üstte), gezinme çubuğu (altta), telefon çerçevesi.
  - Aralarındaki pencerede kayan akış: her post için kullanıcı satırı, 4:5 görsel, simgeler,
    beğeni sayısı, açıklama, yorum bağlantısı ve zaman.

Bir posta "bakılırken" görseli gezinme çubuğunun hemen üstündedir (aşağı kaydırılmış akış):
sinek ekranın yalnızca alt ~%60'ını görür (body/scene.py) ve görsel bu bölgeyi kaplar.
Geçiş türleri:
  - solarak (`fade_to`): eski ekran görüntüsü FADE_MS içinde yenisine karışarak dönüşür.
    Sonraki posta varsayılan geçiş budur (K-030).
  - kaydırarak (`scroll_to`): gerçek telefondaki gibi akış SCROLL_MS içinde, hızlı başlayıp
    yavaşlayarak bir post boyu yukarı kayar. Sinek bunda neredeyse her seferinde kaçar (Z-35);
    deneyler için duruyor.
  - doğrudan (`show`): ekran hemen değişir.

Bakılan postun görseli yerine video da oynatılabilir (`play`); video bitince son karesi kalır.

Tema (THEMES): koyu (Instagram'ın karanlık modu; varsayılan, K-030), açık (Instagram'ın
varsayılanı) ve gri (zemin, post görsellerinin ortalama parlaklığında; gerçek Instagram'da yok,
kontrol için). Sinek, kaydırmada ekrandan geçen geniş açık-koyu alanlardan kaçar (Z-35); tema
bu alanların parlaklığını belirler.

Yazılar insan izleyici içindir; sinek onları yalnızca açık-koyu desen olarak görür.
"""

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BEZEL = 0.022        # çerçeve kalınlığı (genişliğe oranla)
STATUS = 0.08        # durum çubuğu yüksekliği (genişliğe oranla)
HEADER = 0.11
NAV = 0.13
USER_ROW = 0.11
BELOW_IMAGE = 0.38   # görselin altındaki simgeler, beğeni, açıklama, yorum, zaman
POST_ASPECT = 5 / 4  # görsel yükseklik / genişlik
# Kaydırmanın süresi (VARSAYIM; parmakla hızlı kaydırmada akış ~0,3-0,5 sn'de durur).
SCROLL_MS = 400.0
# Sonraki posta solarak geçişin süresi (K-030; ölçülen tek süre).
FADE_MS = 300.0


@dataclass(frozen=True)
class Theme:
    bg: tuple[int, int, int]
    ink: tuple[int, int, int]
    muted: tuple[int, int, int]
    line: tuple[int, int, int]
    avatar: tuple[int, int, int]


# Koyu tema renkleri Instagram'ın karanlık moduna yakın (yaklaşık değerler).
THEMES = {
    "acik": Theme(bg=(255, 255, 255), ink=(20, 20, 20), muted=(142, 142, 142), line=(219, 219, 219),
                  avatar=(200, 200, 200)),
    "koyu": Theme(bg=(0, 0, 0), ink=(245, 245, 245), muted=(168, 168, 168), line=(38, 38, 38),
                  avatar=(60, 60, 60)),
    "gri": Theme(bg=(128, 128, 128), ink=(20, 20, 20), muted=(70, 70, 70), line=(100, 100, 100),
                 avatar=(160, 160, 160)),
}
DEFAULT_THEME = "koyu"  # K-030


@dataclass(frozen=True)
class FeedPost:
    image: np.ndarray
    username: str = "flybrain"
    caption: str = ""
    likes: int = 0


class ScreenSource(Protocol):
    """Telefon ekranını besleyen kaynak: yerel akış (`PhoneFeed`) ya da gerçek ekran
    görüntüleri (`insta/screen.py`, Faz 8). `EmbodiedFly` ikisiyle de çalışır."""

    @property
    def scrolling(self) -> bool: ...

    def show(self, post) -> None: ...

    def fade_to(self, post, now_ms: float, duration_ms: float) -> None: ...

    def scroll_to(self, post, now_ms: float, duration_ms: float) -> None: ...

    def update(self, now_ms: float) -> bool: ...

    def frame(self) -> np.ndarray: ...


@cache
def _font_file() -> str | None:
    """Türkçe harfleri olan bir yazı tipi: matplotlib'in DejaVu Sans'ı (FlyGym ile gelir)."""
    try:
        import matplotlib

        path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
        return str(path) if path.exists() else None
    except ImportError:
        return None


def _font(size: float) -> ImageFont.FreeTypeFont:
    size = max(8, int(size))
    path = _font_file()
    return ImageFont.truetype(path, size) if path else ImageFont.load_default(size=size)


def _printable(text: str) -> str:
    """Varsayılan yazı tipinde olmayan simgeleri (emoji) atar."""
    return "".join(c for c in text if unicodedata.category(c) not in ("So", "Cs", "Co")).strip()


def fit(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Görseli ortadan kırpıp verilen boyuta getirir (Instagram'ın 4:5 kırpması gibi)."""
    img = np.asarray(image)
    if img.dtype != np.uint8:
        img = np.clip(np.round(img * 255), 0, 255).astype(np.uint8)
    if img.ndim == 2:
        img = np.repeat(img[..., None], 3, axis=2)
    h, w = img.shape[:2]
    target = height / width
    if h / w > target:
        ch = int(round(w * target))
        img = img[(h - ch) // 2:(h - ch) // 2 + ch]
    else:
        cw = int(round(h / target))
        img = img[:, (w - cw) // 2:(w - cw) // 2 + cw]
    return np.asarray(Image.fromarray(img).resize((width, height), Image.BILINEAR))


def _px(shape: tuple[int, int]) -> dict[str, int]:
    h, w = shape
    b = int(round(BEZEL * w))
    top = b + int(round((STATUS + HEADER) * w))
    bottom = h - b - int(round(NAV * w))
    inner = w - 2 * b
    return {"h": h, "w": w, "b": b, "top": top, "bottom": bottom, "inner": inner,
            "user": int(round(USER_ROW * w)), "image": int(round(POST_ASPECT * inner)),
            "below": int(round(BELOW_IMAGE * w))}


def post_box(shape: tuple[int, int]) -> tuple[int, int, int, int]:
    """Bakılan postun görselinin ekrandaki yeri: (üst, alt, sol, sağ) piksel."""
    p = _px(shape)
    return p["bottom"] - p["image"], p["bottom"], p["b"], p["w"] - p["b"]


def _heart(d: ImageDraw.ImageDraw, x: float, y: float, s: float, width: int, color: tuple[int, int, int]):
    t = np.linspace(0, 2 * np.pi, 60)
    hx = 16 * np.sin(t) ** 3
    hy = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    d.line(list(zip(x + (hx + 17) / 34 * s, y + (hy + 13) / 31 * s)), fill=color, width=width, joint="curve")


def _chrome(shape: tuple[int, int], theme: Theme) -> np.ndarray:
    """Sabit katman: durum çubuğu, başlık, gezinme çubuğu ve çerçeve."""
    p = _px(shape)
    ink, line = theme.ink, theme.line
    h, w, b = p["h"], p["w"], p["b"]
    left, right = b, w - b
    canvas = Image.new("RGB", (w, h), theme.bg)
    d = ImageDraw.Draw(canvas)
    pad, lw = 0.035 * w, max(1, int(round(w / 270)))
    d.text((left + pad, b + 0.02 * w), "9:41", fill=ink, font=_font(0.04 * w))
    d.rounded_rectangle([right - pad - 0.07 * w, b + 0.025 * w, right - pad, b + 0.055 * w],
                        radius=0.008 * w, outline=ink, width=lw)
    y = b + STATUS * w
    d.text((left + pad, y + 0.02 * w), "Instagram", fill=ink, font=_font(0.065 * w))
    _heart(d, right - pad - 0.06 * w, y + 0.035 * w, 0.055 * w, lw, ink)
    d.line([left, p["top"] - lw, right, p["top"] - lw], fill=line, width=lw)
    bottom = p["bottom"]
    d.line([left, bottom, right, bottom], fill=line, width=lw)
    ny, s = bottom + NAV * w * 0.2, 0.055 * w
    for k in range(5):
        cx = left + p["inner"] * (k + 0.5) / 5
        if k == 0:
            d.polygon([(cx - s / 2, ny + s), (cx - s / 2, ny + s * 0.4), (cx, ny), (cx + s / 2, ny + s * 0.4),
                       (cx + s / 2, ny + s)], outline=ink, width=lw)
        elif k == 1:
            d.ellipse([cx - s / 2, ny, cx + s * 0.3, ny + s * 0.8], outline=ink, width=lw)
            d.line([cx + s * 0.2, ny + s * 0.7, cx + s / 2, ny + s], fill=ink, width=lw)
        elif k == 4:
            d.ellipse([cx - s / 2, ny, cx + s / 2, ny + s], fill=theme.avatar)
        else:
            d.rounded_rectangle([cx - s / 2, ny, cx + s / 2, ny + s], radius=s * 0.25, outline=ink, width=lw)
    d.rounded_rectangle([w * 0.35, h - b - 0.022 * w, w * 0.65, h - b - 0.012 * w], radius=0.005 * w, fill=ink)
    d.rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0), width=b)
    return np.asarray(canvas).copy()


def _post_block(post: FeedPost, shape: tuple[int, int], theme: Theme) -> np.ndarray:
    """Akıştaki bir post: kullanıcı satırı, görsel ve altındakiler (genişlik = iç genişlik)."""
    p = _px(shape)
    ink, muted = theme.ink, theme.muted
    w, inner = p["w"], p["inner"]
    height = p["user"] + p["image"] + p["below"]
    canvas = Image.new("RGB", (inner, height), theme.bg)
    d = ImageDraw.Draw(canvas)
    pad, lw = 0.035 * w, max(1, int(round(w / 270)))
    cy, r = p["user"] / 2, 0.035 * w
    d.ellipse([pad, cy - r, pad + 2 * r, cy + r], fill=theme.avatar, outline=(214, 41, 118), width=lw * 2)
    d.text((pad + 2.6 * r, cy - 0.022 * w), post.username, fill=ink, font=_font(0.04 * w))
    for k in range(3):
        cx = inner - pad - k * 0.018 * w
        d.ellipse([cx - lw, cy - lw, cx + lw, cy + lw], fill=ink)
    canvas.paste(Image.fromarray(fit(post.image, inner, p["image"])), (0, p["user"]))
    y = p["user"] + p["image"] + 0.03 * w
    s = 0.06 * w
    _heart(d, pad, y, s, lw, ink)
    d.ellipse([pad + 1.6 * s, y, pad + 2.6 * s, y + s], outline=ink, width=lw)
    x = pad + 3.2 * s
    d.polygon([(x, y + s * 0.45), (x + s, y), (x + s * 0.6, y + s)], outline=ink, width=lw)
    y += 0.09 * w
    d.text((pad, y), f"{post.likes} beğenme", fill=ink, font=_font(0.037 * w))
    y += 0.055 * w
    caption = _printable(post.caption)
    if caption:
        d.text((pad, y), f"{post.username} {caption}"[:42], fill=ink, font=_font(0.037 * w))
    y += 0.055 * w
    d.text((pad, y), "Tüm yorumları gör", fill=muted, font=_font(0.034 * w))
    y += 0.05 * w
    d.text((pad, y), "2 saat önce", fill=muted, font=_font(0.03 * w))
    return np.asarray(canvas).copy()


def ease_out(x: float) -> float:
    return 1.0 - (1.0 - x) ** 3


class PhoneFeed:
    """Kaydırılabilir akış ve ekran görüntüsü; zaman simülasyon saatinden gelir."""

    def __init__(self, shape: tuple[int, int], previous: FeedPost | None = None, theme: str = DEFAULT_THEME):
        """previous: bakılan posttan önceki post (üst kısmı ekranda görünür); theme: THEMES anahtarı."""
        self.shape = shape
        self.theme = theme
        self._theme = THEMES[theme]
        self._p = _px(shape)
        self._chrome = _chrome(shape, self._theme)
        self._blocks: list[np.ndarray] = []
        self._starts: list[int] = []
        self._length = 0
        self._strip: np.ndarray | None = None
        self.index = -1
        self._offset = 0.0
        self._scroll: tuple[float, float, float, float] | None = None  # başlangıç, hedef, t0, süre
        self._fade: tuple[np.ndarray, float, float] | None = None  # eski kare, t0, süre
        self._fade_alpha = 1.0
        self._video: tuple[Callable[[float], np.ndarray | None], float] | None = None
        self._video_frame: np.ndarray | None = None
        self._changed = True
        if previous is not None:
            self._append(previous)
            self.index = 0
            self._offset = self._aligned(0)

    def _append(self, post: FeedPost) -> int:
        block = _post_block(post, self.shape, self._theme)
        self._blocks.append(block)
        self._starts.append(self._length)
        self._length += len(block)
        self._strip = None
        return len(self._blocks) - 1

    def _aligned(self, i: int) -> float:
        """Post i'nin görseli gezinme çubuğunun hemen üstündeyken akışın kayma miktarı."""
        p = self._p
        return self._starts[i] + p["user"] + p["image"] - (p["bottom"] - p["top"])

    @property
    def scrolling(self) -> bool:
        return self._scroll is not None or self._fade is not None

    @property
    def post_height(self) -> int:
        """Akışta bir postun boyu (sonraki posta kaydırma mesafesi, piksel)."""
        p = self._p
        return p["user"] + p["image"] + p["below"]

    @property
    def image_shape(self) -> tuple[int, int]:
        """Post görselinin piksel boyutu (yükseklik, genişlik)."""
        return self._p["image"], self._p["inner"]

    def _stop_video(self) -> None:
        self._video = None
        self._video_frame = None

    def show(self, post: FeedPost) -> None:
        """Yeni postu akışa ekler ve kaydırmadan ona geçer."""
        self.index = self._append(post)
        self._offset = self._aligned(self.index)
        self._scroll = None
        self._stop_video()
        self._changed = True

    def scroll_to(self, post: FeedPost, now_ms: float, duration_ms: float = SCROLL_MS) -> None:
        """Yeni postu akışa ekler ve kaydırarak ona geçer."""
        self.index = self._append(post)
        self._scroll = (self._offset, self._aligned(self.index), now_ms, duration_ms)
        self._stop_video()
        self._changed = True

    def fade_to(self, post: FeedPost, now_ms: float, duration_ms: float = FADE_MS) -> None:
        """Yeni postu akışa ekler; ekran eski görüntüden yenisine solarak geçer."""
        old = self.frame()
        self.show(post)
        self._fade = (old, now_ms, duration_ms)
        self._fade_alpha = 0.0

    def play(self, video: Callable[[float], np.ndarray | None], now_ms: float) -> None:
        """Bakılan postun görselinde video oynatır.

        video(t_ms): başlangıçtan t_ms sonraki kare (image_shape boyutunda, uint8) ya da
        video bittiyse None.
        """
        self._video = (video, now_ms)

    def update(self, now_ms: float) -> bool:
        """Kaydırmayı ilerletir; ekran görüntüsü değiştiyse True."""
        if self._scroll is not None:
            start, end, t0, dur = self._scroll
            x = min(1.0, max(0.0, (now_ms - t0) / dur))
            offset = start + (end - start) * ease_out(x)
            if x >= 1.0:
                self._scroll = None
            if int(round(offset)) != int(round(self._offset)):
                self._changed = True
            self._offset = offset
        if self._fade is not None:
            _, t0, dur = self._fade
            self._fade_alpha = min(1.0, max(0.0, (now_ms - t0) / dur))
            self._changed = True
            if self._fade_alpha >= 1.0:
                self._fade = None
        if self._video is not None:
            video, t0 = self._video
            f = video(now_ms - t0)
            if f is None:
                self._video = None
            else:
                self._video_frame = f
                self._changed = True
        changed, self._changed = self._changed, False
        return changed

    def frame(self) -> np.ndarray:
        p = self._p
        if self._strip is None:
            self._strip = np.concatenate(self._blocks) if self._blocks else np.zeros((0, p["inner"], 3), np.uint8)
        out = self._chrome.copy()
        view = p["bottom"] - p["top"]
        window = np.empty((view, p["inner"], 3), np.uint8)
        window[:] = self._theme.bg
        o = int(round(self._offset))
        lo, hi = max(o, 0), min(o + view, len(self._strip))
        if hi > lo:
            window[lo - o:hi - o] = self._strip[lo:hi]
        if self._video_frame is not None:
            y = self._starts[self.index] + p["user"] - o
            a, b = max(y, 0), min(y + p["image"], view)
            if b > a:
                window[a:b] = self._video_frame[a - y:b - y]
        out[p["top"]:p["bottom"], p["b"]:p["w"] - p["b"]] = window
        if self._fade is not None:
            a = self._fade_alpha
            out = np.round((1 - a) * self._fade[0] + a * out).astype(np.uint8)
        return out
