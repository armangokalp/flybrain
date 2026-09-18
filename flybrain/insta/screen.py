"""Gerçek ekran görüntülerini sineğin telefon ekranına basar (Faz 8).

Yerel akışta (`body/phone.py`) ekranı biz çiziyoruz: çerçeve, post bloğu, kaydırma. Gerçek
Instagram'da ekranın kendisi hazır geliyor; bu sınıf yalnızca kareyi tutar ve postlar arasında
**solarak** geçer (K-030). Geçiş sineğin gördüğü ekranda olur; tarayıcı asıl kaydırmayı solma
sürerken, perde arkasında yapar. Sinek gerçek kaydırmayı hiç görmez (Z-35).

Ekran kaynağı arayüzü `body/phone.py` içindeki `ScreenSource`; `EmbodiedFly` ikisini de kabul eder.
"""

from dataclasses import dataclass

import numpy as np

from flybrain.body.phone import FADE_MS, fit


@dataclass(frozen=True)
class Shot:
    """Telefonun tam ekran görüntüsü (yerel akıştaki `FeedPost`'un karşılığı)."""

    image: np.ndarray
    caption: str = ""      # postun açıklaması (koku olarak verilir)
    username: str = ""


class ScreenshotFeed:
    """Ekranda duran kare; yeni kareye solarak geçer."""

    def __init__(self, shape: tuple[int, int]):
        self.shape = shape
        self._frame = np.zeros((*shape, 3), np.uint8)
        self._fade: tuple[np.ndarray, float, float] | None = None  # eski kare, t0, süre
        self._fade_alpha = 1.0
        self._video: tuple | None = None  # (kare fonksiyonu, t0)
        self._changed = True

    def _fitted(self, shot: Shot | np.ndarray) -> np.ndarray:
        image = shot.image if isinstance(shot, Shot) else shot
        h, w = self.shape
        image = np.asarray(image)
        return image if image.shape[:2] == (h, w) else fit(image, w, h)

    @property
    def scrolling(self) -> bool:
        return self._fade is not None

    def show(self, shot: Shot | np.ndarray) -> None:
        """Ekranı hemen değiştirir (geçiş yok)."""
        self._frame = self._fitted(shot)
        self._fade = None
        self._fade_alpha = 1.0
        self._video = None  # önceki postun videosu burada biter
        self._changed = True

    def fade_to(self, shot: Shot | np.ndarray, now_ms: float, duration_ms: float = FADE_MS) -> None:
        """Ekran eski kareden yenisine solarak geçer. Süre 0 ise anında değişir (K-039)."""
        if duration_ms <= 0.0:
            self.show(shot)
            return
        old = self.frame()
        self.show(shot)
        self._fade = (old, now_ms, duration_ms)
        self._fade_alpha = 0.0

    def scroll_to(self, shot: Shot | np.ndarray, now_ms: float, duration_ms: float = FADE_MS) -> None:
        raise NotImplementedError("gerçek ekranda kaydırma yok: tarayıcı perde arkasında kaydırır (K-030)")

    def play(self, video, now_ms: float) -> None:
        """Ekranda video oynatır (reels). `video(t_ms)` kareyi ya da bittiyse None döndürür.

        Kareler tarayıcıdan önceden toplanıyor ve burada **simülasyon zamanıyla** oynatılıyor:
        tarayıcı gerçek zamanda oynarken simülasyon ~3 kat yavaş ilerlediği için sinek videoyu
        hızlanmış görürdü (Z-37). Video bitince son karesi ekranda kalır.
        """
        self._video = (video, now_ms)

    def update(self, now_ms: float) -> bool:
        """Geçişi ilerletir; ekran değiştiyse True."""
        if self._video is not None:
            video, t0 = self._video
            kare = video(now_ms - t0)
            if kare is None:
                self._video = None
            else:
                self._frame = self._fitted(kare)
                self._changed = True
        if self._fade is not None:
            _, t0, dur = self._fade
            self._fade_alpha = min(1.0, max(0.0, (now_ms - t0) / dur))
            self._changed = True
            if self._fade_alpha >= 1.0:
                self._fade = None
        changed, self._changed = self._changed, False
        return changed

    def frame(self) -> np.ndarray:
        if self._fade is None:
            return self._frame
        a = self._fade_alpha
        return np.round((1 - a) * self._fade[0] + a * self._frame).astype(np.uint8)
