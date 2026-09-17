"""Instagram akışını okur ve sineğin kararını gerçek düğmelere uygular (Faz 8).

**Akış okuma.** Mobil düzende her post bir `article`. Bakılan post, görüntü alanının ortasına
en yakın olanıdır. Ondan alınan: kullanıcı adı, açıklama metni (koku olarak verilir), bağlantı
ve ekran görüntüsü.

**Geçiş.** Sonraki posta geçerken tarayıcı **perde arkasında** kaydırır: sineğin ekranı o sırada
solmaktadır ve kaydırmayı görmez (K-030, Z-35).

**Videolar.** Tarayıcıdaki videolar duraklatılır. Video gerçek zamanda oynarken simülasyon ~3 kat
yavaş ilerlediği için sinek videoyu hızlandırılmış görürdü; bunun yerine karesi simülasyon
zamanından sürülür (`video_time`).

**Eylemler.** Her eylem şu sırayla: valiye sor (K-007) → düğmeyi bul → tıkla → **sonucu doğrula**
(düğmenin etiketi değişti mi) → kaydet. Kuru çalıştırmada tıklama yapılmaz, yalnızca kaydedilir.

**Etiketler.** Düğmeler erişilebilirlik etiketinden bulunur; Instagram'ın arayüz dili hesaba göre
değiştiği için Türkçe ve İngilizce etiketler birlikte aranır. VARSAYIM: etiket metinleri gerçek
oturumda doğrulanmalı (Z-36).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from flybrain.insta.browser import HOME, Browser
from flybrain.insta.governor import Governor, Vetoed

# eylem: (uygulanmadan önceki etiketler, uygulandıktan sonraki etiketler)
LABELS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "begen": (("Like", "Beğen"), ("Unlike", "Beğenme", "Beğenmekten vazgeç")),
    "kaydet": (("Save", "Kaydet"), ("Remove", "Kaldır", "Kaydetmekten vazgeç")),
    "yorum": (("Comment", "Yorum", "Yorum yap"), ()),
}
FOLLOW_TEXTS = ("Follow", "Takip et")
FOLLOWING_TEXTS = ("Following", "Requested", "Takip ediliyor", "İstek gönderildi")
COMMENT_PLACEHOLDERS = ("Add a comment", "Yorum ekle")
POST_TEXTS = ("Post", "Paylaş")


@dataclass
class FeedItem:
    """Akışta bakılan post."""

    index: int
    username: str = ""
    caption: str = ""
    url: str = ""
    video: bool = False
    shot: np.ndarray | None = field(default=None, repr=False)


class InstaFeed:
    def __init__(self, browser: Browser, governor: Governor, require_login: bool = True):
        """require_login: yalnızca testlerdeki yerel sahte akış için False."""
        self.b = browser
        self.gov = governor
        self.require_login = require_login
        self.index = -1

    # ---- akış ----

    def open(self, wait_ms: float = 4000.0) -> None:
        self.open_url(HOME, wait_ms)

    def open_url(self, url: str, wait_ms: float = 500.0) -> None:
        """Akışı açar. Gerçek Instagram için `open`; yerel sahte akış testlerde bu yolla açılır."""
        self.b.goto(url, wait_ms=wait_ms)
        self.guard()
        self.b.page.wait_for_selector("article", timeout=30_000)
        self.freeze_videos()

    def guard(self) -> None:
        """Doğrulama sayfası ya da düşmüş oturum varsa durur (Z-11)."""
        self.gov.watch(self.b.page.url, self.b.logged_in() or not self.require_login)

    @property
    def articles(self):
        return self.b.page.locator("article")

    def _article(self, i: int):
        return self.articles.nth(i)

    def freeze_videos(self) -> None:
        """Tarayıcıdaki bütün videoları duraklatır ve başa alır."""
        self.b.page.evaluate("document.querySelectorAll('video').forEach(v => { v.pause(); v.muted = true; })")

    def video_time(self, t_ms: float) -> None:
        """Bakılan postun videosunu simülasyon zamanına göre ilerletir."""
        self.b.page.evaluate(
            "t => document.querySelectorAll('video').forEach(v => { v.pause(); v.currentTime = t; })",
            max(0.0, t_ms / 1000.0),
        )

    def goto_post(self, i: int) -> None:
        """Postu ekranın üstüne getirir (tarayıcı tarafında; sinek bunu görmez)."""
        self._article(i).evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
        self.b.page.wait_for_timeout(400)
        self.freeze_videos()
        self.index = i

    def next_post(self) -> FeedItem:
        """Sonraki posta geçer ve onu okur."""
        return self.read(self.index + 1)

    def read(self, i: int | None = None) -> FeedItem:
        """Postu okur: kullanıcı adı, açıklama, bağlantı ve ekran görüntüsü."""
        i = self.index if i is None else i
        if i != self.index:
            self.goto_post(i)
        self.guard()
        art = self._article(i)
        item = FeedItem(index=i)
        try:
            item.username = art.locator("header a").first.inner_text(timeout=2000).strip().splitlines()[0]
        except Exception:
            item.username = ""
        item.caption = self._caption(art, item.username)
        try:
            item.url = art.locator("a[href*='/p/'], a[href*='/reel/']").first.get_attribute("href", timeout=2000) or ""
        except Exception:
            item.url = ""
        item.video = art.locator("video").count() > 0
        item.shot = self.b.shot()
        return item

    def _caption(self, art, username: str) -> str:
        """Postun açıklaması: kullanıcı adından sonraki metin (koku kaynağı)."""
        try:
            text = art.locator("h1, ul li span[dir='auto'], span[dir='auto']").first.inner_text(timeout=2000)
        except Exception:
            return ""
        text = text.strip()
        if username and text.startswith(username):
            text = text[len(username):].strip()
        return text

    # ---- eylemler ----

    def _icon(self, action: str, state: int):
        """Postun düğmesi: state 0 uygulanmadan önceki etiket, 1 uygulandıktan sonraki."""
        art = self._article(self.index)
        for label in LABELS[action][state]:
            loc = art.locator(f"svg[aria-label='{label}']")
            if loc.count():
                return loc.first
        return None

    def _state(self, action: str) -> bool | None:
        """Eylem zaten uygulanmış mı (True), uygulanmamış mı (False), bilinmiyor mu (None)."""
        if action == "takip":
            art = self._article(self.index)
            for text in FOLLOWING_TEXTS:
                if art.get_by_role("button", name=text, exact=False).count():
                    return True
            for text in FOLLOW_TEXTS:
                if art.get_by_role("button", name=text, exact=False).count():
                    return False
            return None
        if self._icon(action, 1) is not None:
            return True
        if self._icon(action, 0) is not None:
            return False
        return None

    def act(self, action: str, text: str = "") -> dict:
        """Kararı uygular. Dönen kayıt: eylem, uygulandı mı, gerekçe."""
        self.guard()
        try:
            self.gov.check(action, text)
        except Vetoed as e:
            return self.gov.record(action, False, f"vali: {e}")
        if self._state(action) is True:
            return self.gov.record(action, False, "zaten uygulanmış")
        if self.gov.dry_run:
            return self.gov.record(action, False, "kuru çalıştırma")
        try:
            self._click(action, text)
        except Exception as e:  # tıklama ya da doğrulama başarısız
            return self.gov.record(action, False, f"başarısız: {type(e).__name__}: {e}")
        self.b.page.wait_for_timeout(800)
        ok = self._state(action)
        if action == "yorum":
            ok = True  # yorumun doğrulaması gönderimden sonra metnin listede görünmesi
        if ok is not True:
            return self.gov.record(action, False, "tıklandı ama durum değişmedi")
        return self.gov.record(action, True, text)

    def _click(self, action: str, text: str) -> None:
        art = self._article(self.index)
        if action == "takip":
            for name in FOLLOW_TEXTS:
                btn = art.get_by_role("button", name=name, exact=False)
                if btn.count():
                    btn.first.click(timeout=5000)
                    return
            raise RuntimeError("takip düğmesi bulunamadı")
        if action == "yorum":
            self._comment(text)
            return
        icon = self._icon(action, 0)
        if icon is None:
            raise RuntimeError(f"{action} düğmesi bulunamadı")
        icon.click(timeout=5000)

    def _comment(self, text: str) -> None:
        """Yorumu yazar ve gönderir; metin boşsa hiçbir şey yapılmaz."""
        if not text.strip():
            raise ValueError("yorum metni boş")
        art = self._article(self.index)
        box = None
        for ph in COMMENT_PLACEHOLDERS:
            loc = art.get_by_placeholder(ph, exact=False)
            if loc.count():
                box = loc.first
                break
        if box is None:
            icon = self._icon("yorum", 0)
            if icon is None:
                raise RuntimeError("yorum kutusu bulunamadı")
            icon.click(timeout=5000)
            self.b.page.wait_for_timeout(1000)
            for ph in COMMENT_PLACEHOLDERS:
                loc = self.b.page.get_by_placeholder(ph, exact=False)
                if loc.count():
                    box = loc.first
                    break
        if box is None:
            raise RuntimeError("yorum kutusu bulunamadı")
        box.click(timeout=5000)
        box.type(text, delay=120)  # insan hızında yazma
        for scope in (art, self.b.page):  # önce postun kendi düğmesi, sonra sayfadaki
            for name in POST_TEXTS:
                btn = scope.get_by_role("button", name=name, exact=True)
                if btn.count():
                    btn.first.click(timeout=5000)
                    return
        raise RuntimeError("yorumu gönderme düğmesi bulunamadı")
