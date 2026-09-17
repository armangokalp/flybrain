"""Instagram'ı süren tarayıcı (Faz 8, K-006).

- **Kalıcı profil:** Giriş kullanıcı tarafından elle yapılır; kod şifre görmez, yazmaz ve okumaz.
  Çerezler `browser-profile/` altında kalır (gitignore'da).
- **Telefon görünümü:** Görüntü alanı sanal telefonla aynı oranda (19,5:9). Instagram'ın mobil
  düzeni sineğin gördüğü ekrana birebir oturuyor; story yükleme de yalnızca bu düzende var.
- **Karanlık mod:** Solarak geçişin kaçışı önlediği ölçüm karanlık modda yapıldı (K-030).
- **Görünür pencere:** Otomasyon izlenebilsin ve güvenlik doğrulaması çıkarsa kullanıcı elle
  çözebilsin diye (Z-11). Başsız kip yalnızca testler için.
- **Azaltılmış hareket:** Sayfaya `prefers-reduced-motion` verilir; site kendi animasyonlarını
  kısarsa sinek daha az ani parlaklık değişimi görür (Z-25).

Bu modül yalnızca sayfayı açar ve ekran görüntüsü alır. Eylemler `insta/actions.py` içinde.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from flybrain.paths import ROOT

PROFILE = ROOT / "browser-profile"
HOME = "https://www.instagram.com/"
# iPhone'un mantıksal görüntü alanı; sanal telefonun oranı (19,5:9) ile aynı.
VIEWPORT = {"width": 390, "height": 844}
SCALE = 2  # ekran görüntüsü iki kat çözünürlükte alınır, sonra ekrana küçültülür
UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


class Browser:
    """Kalıcı profille açılan, telefon görünümünde tek sekmeli tarayıcı."""

    def __init__(self, profile: Path | str = PROFILE, headless: bool = False, slow_mo_ms: float = 0.0):
        self.profile = Path(profile)
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self._pw = None
        self.context = None
        self.page = None

    def open(self) -> "Browser":
        from playwright.sync_api import sync_playwright

        if self.page is not None:
            return self
        self.profile.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self.context = self._pw.chromium.launch_persistent_context(
            str(self.profile),
            channel="chromium",  # başsız kipte de tam tarayıcı (ayrı "headless shell" indirilmedi)
            headless=self.headless,
            slow_mo=self.slow_mo_ms,
            viewport=VIEWPORT,
            device_scale_factor=SCALE,
            user_agent=UA,
            is_mobile=True,
            has_touch=True,
            color_scheme="dark",
            # Animasyonlar açık: sinek kendi beğenisinin kalbini ve yorumunun yazılışını
            # görsün (kullanıcı kararı). Kapalıyken eylemin tek izi düğmenin renk değişimiydi.
            reduced_motion="no-preference",
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        return self

    def __enter__(self) -> "Browser":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def _live(self):
        if self.page is None:
            raise RuntimeError("tarayıcı açık değil: önce open() çağır")
        return self.page

    def goto(self, url: str = HOME, wait_ms: float = 3000.0) -> None:
        page = self._live
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)  # akışın yüklenmesi

    def logged_in(self) -> bool:
        """Profilde Instagram oturum çerezi var mı? (çerezin değeri okunmaz)"""
        if self.context is None:
            return False
        return any(c["name"] == "sessionid" and "instagram" in c["domain"] for c in self.context.cookies())

    def shot(self) -> np.ndarray:
        """Görüntü alanının ekran görüntüsü (yükseklik, genişlik, 3) uint8."""
        png = self._live.screenshot(type="png")
        import io

        return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))

    def screen(self, shape: tuple[int, int]) -> np.ndarray:
        """Ekran görüntüsü, sanal telefonun doku boyutuna (yükseklik, genişlik) küçültülmüş."""
        from flybrain.body.phone import fit

        h, w = shape
        return fit(self.shot(), w, h)

    def close(self) -> None:
        if self.context is not None:
            self.context.close()
        if self._pw is not None:
            self._pw.stop()
        self._pw = self.context = self.page = None
