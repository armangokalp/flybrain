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

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

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
# Girişten sonra çıkan kutular. Yalnızca **reddeden** seçeneğe basılır; hiçbir şey kabul edilmez.
DISMISS_TEXTS = ("Not now", "Not Now", "Şimdi değil", "Şu an değil")
# Web'e özel "Use the app" reklam bandı ve kapatma düğmesinin metni (Z-38).
APP_BANNER_TEXTS = ("Use the app", "Uygulamayı kullan")
CLOSE_TEXTS = ("Close", "Kapat")
# Açıklama okunurken atlanacak satırlar (gerçek sayfadan: beğeni sayısı, "more", zaman damgası).
SKIP_LINES = ("more", "less", "daha fazla", "daha az", "Verified", "Onaylanmış", "Translate", "Çevir")
SKIP_PREFIX = ("Liked by", "Beğenen", "View all", "Tüm yorum", "Add a comment", "Yorum ekle",
               "Original audio", "Orijinal ses", "Follow", "Takip et", "Suggested for you",
               "Senin için önerilen", "Sponsored", "Sponsorlu", "Paid partnership", "Reels")
_TIME_LINE = re.compile(r"^\d+\s*(saniye|dakika|saat|gün|hafta|second|minute|hour|day|week)", re.I)
# Sayaç satırları: "89K", "277.4K", "1,234"; ve "and 5 others" gibi beğeni satırının kuyruğu.
_COUNT_LINE = re.compile(r"^\d[\d.,\s]*[KMBkmb]?$")
# Gezinme çubuğunun yüksekliği (CSS piksel). Sanal telefonda NAV oranı 0,13 × genişlik;
# 390 piksellik görüntü alanında ~51 piksel (body/phone.py).
NAV_PX = 51
ALIGN_TOL_PX = 8    # hizalamada kabul edilen sapma
# Reels: tarayıcıdan toplanan video penceresi. 2 sn, sineğin bir posta baktığı süreye yakın.
VIDEO_MS = 2000.0
VIDEO_FPS = 15.0
VIDEO_SEEK_MS = 60.0  # currentTime değişince karenin çizilmesi için beklenen süre
# Eylem animasyonu (beğeni kalbi, yorumun belirmesi): tarayıcıdan gerçek zamanda çekilir.
ACTION_MS = 900.0
ACTION_FPS = 12.0
DOUBLE_TAP_MS = 90.0  # çift dokunmanın iki vuruşu arası
ALIGN_SKIP_PX = 40  # bundan büyük sapmada post atlanır: sinek fotoğrafı göremezdi
_OTHERS_LINE = re.compile(r"^(and|ve)\s+[\d.,]+\s*(others|diğer)", re.I)


@dataclass
class FeedItem:
    """Akışta bakılan post."""

    index: int
    username: str = ""
    caption: str = ""
    url: str = ""
    video: bool = False
    shot: np.ndarray | None = field(default=None, repr=False)
    akisa_donuldu: bool = False  # bu postu bulmadan önce akıştan düşmüştük (Z-38)
    sapma: float = 0.0  # görselin alt kenarının hedeften kalan uzaklığı (piksel)


class InstaFeed:
    def __init__(self, browser: Browser, governor: Governor, require_login: bool = True):
        """require_login: yalnızca testlerdeki yerel sahte akış için False."""
        self.b = browser
        self.gov = governor
        self.require_login = require_login
        self.index = -1
        self.home: str | None = None  # akışın adresi; ilk açılışta yakalanır
        self.seen: set[str] = set()  # gösterilmiş postların bağlantıları
        self.atlanan: list[tuple[str, float]] = []  # hizalanamadığı için atlananlar
        # Tarayıcının karesini dışarı veren kanca (canlı izleme). Sinek bu kareleri görmüyor:
        # asıl kaydırma perde arkasında oluyor, sineğin ekranı solarak geçiyor (Z-35).
        self.on_frame = None
        self.last_frames: list = []  # son eylemin animasyon kareleri

    # ---- akış ----

    def open(self, wait_ms: float = 4000.0) -> None:
        self.open_url(HOME, wait_ms)

    def open_url(self, url: str, wait_ms: float = 500.0) -> None:
        """Akışı açar. Gerçek Instagram için `open`; yerel sahte akış testlerde bu yolla açılır."""
        self.home = url  # akıştan düşersek buraya dönülür
        self.b.goto(url, wait_ms=wait_ms)
        self.guard()
        self.dismiss_dialogs()
        self.b.page.wait_for_selector("article", timeout=30_000)
        self.dismiss_app_banner()
        self.freeze_videos()

    def on_feed(self) -> bool:
        """Tarayıcı hâlâ akışta mı?

        Instagram sineği akıştan çıkarabiliyor: ilk hizalı oturumda, girişimizin tetiklediği
        güvenlik uyarısı yüzünden ~3 saniye bildirim sayfası açık kaldı (Z-38). Kod bunu fark
        etmeyince sinek post sandığı şeyin yerine o sayfayı gördü.
        """
        if self.home is None:  # akış bu yolla açılmadıysa (testlerdeki sahte akış) buradayız
            self.home = self.b.page.url
        return (urlparse(self.b.page.url).path == urlparse(self.home).path
                and self.articles.count() > 0)

    def ensure_feed(self) -> bool:
        """Akıştan düşmüşsek geri döner; geri dönmek gerektiyse True."""
        if self.on_feed():
            return False
        self.open_url(self.home)
        return True

    def dismiss_app_banner(self) -> bool:
        """Sayfanın altındaki "Use the app" reklam bandını kapatır.

        Band gezinme çubuğunun hemen üstünde duruyor (ölçülen: y 759-794, yükseklik 35) ve
        hizalanan postun alt kenarını örtüyor; sinek fotoğrafın alt şeridi yerine parlak bir
        çizgi görüyor. Yalnızca web'de var, gerçek uygulamada yok (Z-38).
        """
        return bool(self.b.page.evaluate(
            """(texts) => {
                const it = document.createNodeIterator(document.body, NodeFilter.SHOW_TEXT);
                let n;
                while ((n = it.nextNode())) {
                    if (!texts.includes((n.nodeValue || '').trim())) continue;
                    let el = n.parentElement;
                    for (let k = 0; k < 5 && el; k++, el = el.parentElement) {
                        const btn = [...el.querySelectorAll('[role=button], button')].find(
                            x => CLOSE.includes((x.textContent || '').trim()));
                        if (btn) { btn.click(); return true; }
                    }
                }
                return false;
            }""".replace("CLOSE", repr(list(CLOSE_TEXTS)).replace("'", '"')),
            list(APP_BANNER_TEXTS),
        ))

    def dismiss_dialogs(self) -> list[str]:
        """Akışın önünü kapatan kutuları kapatır ("Giriş bilgilerini kaydet?" gibi).

        Yalnızca **reddeden** düğmeye basılır ("Not now"); hiçbir şey kabul edilmez, kaydedilmez.
        Kapatılmazsa sinek akış yerine kutuyu görür (ilk kuru çalıştırmada olan buydu).
        """
        kapatilan = []
        for text in DISMISS_TEXTS:
            btn = self.b.page.get_by_role("button", name=text, exact=True)
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=3000)
                kapatilan.append(text)
                self.b.page.wait_for_timeout(600)
        return kapatilan

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
        """Videoları simülasyon zamanına göre ilerletir.

        Sayfadaki **bütün** videolara uygulanıyor: görünür olan yalnızca bakılan post ama
        ötekilerin de kendi başlarına oynamaması gerekiyor.
        """
        self.b.page.evaluate(
            "t => document.querySelectorAll('video').forEach(v => { v.pause(); v.currentTime = t; })",
            max(0.0, t_ms / 1000.0),
        )

    def grab_video(self, duration_ms: float = VIDEO_MS, fps: float = VIDEO_FPS) -> list[np.ndarray]:
        """Bakılan postun videosunu tarayıcıdan **kare kare** toplar (reels).

        Video tarayıcıda kendi başına oynarsa sinek onu ~3 kat hızlanmış görür (Z-37): simülasyon
        gerçek zamandan o kadar yavaş. Bunun yerine kareler burada toplanıp sineğe simülasyon
        zamanıyla oynatılıyor (`ScreenshotFeed.play`). Videonun süresi yetmiyorsa başa dönülür;
        Instagram'da reels zaten döngüde oynuyor.
        """
        # Bakılan postun videosu: sayfadaki ilk video başka bir posta ait olabilir.
        art = self._article_of(self.index)
        sure = art.evaluate(
            "(el) => { const v = el.querySelector('video'); return v ? v.duration : 0; }") or 0.0
        if not sure or not np.isfinite(sure):
            return []
        kareler = []
        n = max(1, int(round(duration_ms / 1000.0 * fps)))
        for k in range(n):
            self.video_time((k / fps % sure) * 1000.0)
            self.b.page.wait_for_timeout(VIDEO_SEEK_MS)  # karenin çizilmesini bekle
            kareler.append(self.b.shot())
        self.video_time(0.0)
        return kareler

    def grab_frames(self, duration_ms: float = ACTION_MS, fps: float = ACTION_FPS) -> list:
        """Tarayıcıyı gerçek zamanda kare kare çeker: eylemin animasyonu (beğeni kalbi).

        Kareler sonra sineğe simülasyon zamanıyla oynatılıyor; sinek kendi eyleminin sonucunu
        görüyor (kullanıcı kararı). Yakalama süresi animasyonun uzunluğu kadar.
        """
        kareler = []
        araliq = 1000.0 / fps
        for _ in range(max(1, int(round(duration_ms / araliq)))):
            kareler.append(self.b.shot())
            if self.on_frame is not None:
                self.on_frame(kareler[-1])
            self.b.page.wait_for_timeout(araliq)
        return kareler

    def _emit(self) -> None:
        if self.on_frame is not None:
            self.on_frame(self.b.shot())

    def _article_of(self, i: int, url: str = ""):
        """Postun `article`'ı. Bağlantı verilirse indeks yerine ona göre bulunur.

        Instagram akışın başından `article` siliyor, yani indeksler iş yaparken kayıyor: aynı
        `i` bir an sonra başka bir posta bakıyor. Ölçülen sonuç, aynı postun bir oturumda üç
        kez çıkmasıydı (Z-38).
        """
        if url:
            loc = self.articles.filter(has=self.b.page.locator(f'a[href="{url}"]'))
            if loc.count():
                return loc.first
        return self._article(i)

    def goto_post(self, i: int, url: str = "") -> None:
        """Postun **görselini** sineğin baktığı bölgeye getirir (tarayıcı tarafında).

        Sinek ekranın alt bölümünü görüyor (telefon zemine gömülü, body/scene.py). Yerel akışta
        bakılan postun görseli gezinme çubuğunun hemen üstüne yerleştiriliyor (body/phone.py);
        gerçek sayfada da aynı hizaya getiriliyor. Yoksa sinek fotoğrafı değil, altındaki beğeni
        ve açıklama satırlarını görüyor.
        """
        # Hizaladıktan sonra sayfa kayabiliyor: görsel yüklenip büyüyor, karusel yeniden
        # boyutlanıyor. Sapma kapanana kadar yineleniyor (ölçülen: karusellerde 48 piksel).
        self.dismiss_app_banner()  # band hizaya değil ama sineğin gördüğüne karışıyor (Z-38)
        for _ in range(4):
            hiza = self._align(i, url)
            self.b.page.wait_for_timeout(400)
            self._emit()  # kaydırmayı izleyiciye göster
            if hiza is not None and abs(hiza["sapma"]) <= ALIGN_TOL_PX:
                break
        self.freeze_videos()
        self.index = i

    def _align(self, i: int, url: str = "") -> dict | None:
        """Postun en büyük görselinin alt kenarını gezinme çubuğunun üstüne hizalar."""
        return self._article_of(i, url).evaluate(
            """(el, nav) => {
                const media = [...el.querySelectorAll('img, video')];
                let best = null, area = 0;
                for (const m of media) {
                    const r = m.getBoundingClientRect();
                    if (r.width * r.height > area) { area = r.width * r.height; best = m; }
                }
                if (!best) { el.scrollIntoView({block: 'start', behavior: 'instant'}); return null; }
                const r = best.getBoundingClientRect();
                const sapma = r.bottom - (window.innerHeight - nav);
                window.scrollBy(0, sapma);
                return {ust: r.top, alt: r.bottom, yukseklik: r.height, sapma};
            }""",
            NAV_PX,
        )

    def _load_more(self) -> None:
        """Akışın sonuna inip yeni postların yüklenmesini bekler.

        **Sayfanın** en altına iniliyor, son makalenin sonuna değil. Instagram takip edilen
        hesapların postları bitince "You're all caught up" ayracı koyup altına önerilen postları
        yüklüyor. Akışta tek post kaldığında o postun sonu sayfanın altına ulaşmıyor, sonsuz
        kaydırma tetiklenmiyor ve akış orada kilitleniyordu (ölçüm: 6 turda makale sayısı 1'de
        kaldı, sayfada "You're all caught up" yazıyordu).
        """
        self.b.page.evaluate(
            "window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'})")
        self.b.page.wait_for_timeout(1500)

    def next_post(self) -> FeedItem:
        """Sıradaki **görülmemiş** postu bulur ve okur.

        İndeksle ilerlemek yetmiyor: Instagram postları kaydırdıkça yüklüyor ve listeyi yeniden
        düzenleyebiliyor. Bu yüzden post bağlantısı ölçüt alınıyor.
        """
        donuldu = self.ensure_feed()
        for _ in range(8):
            for i in range(self.articles.count()):
                url = self._post_url(self._article(i))
                if url and url not in self.seen:
                    self.seen.add(url)
                    self.goto_post(i, url)
                    item = self.read(i, url)
                    if abs(item.sapma) > ALIGN_SKIP_PX:
                        # Hizalanamayan post: sinek fotoğrafı değil üstündeki satırları görürdü.
                        # Akışın ilk postunda oluyor — görseli sayfanın üstünde kalıyor ve sayfa
                        # zaten en üstte olduğu için aşağı itilemiyor (ölçülen: -348 px, Z-38).
                        self.atlanan.append((url, item.sapma))
                        continue
                    item.akisa_donuldu = donuldu
                    return item
            self._load_more()
        raise RuntimeError("akışta yeni post bulunamadı")

    def read(self, i: int | None = None, url: str = "") -> FeedItem:
        """Postu okur: kullanıcı adı, açıklama, bağlantı ve ekran görüntüsü.

        `url` verilirse post indeksle değil bağlantısıyla bulunur; akış iş yaparken kaysa bile
        okunan, hizalanan ve ekran görüntüsü alınan hep aynı post olur (Z-38).
        """
        i = self.index if i is None else i
        if i != self.index and not url:
            self.goto_post(i)
        self.guard()
        art = self._article_of(i, url)
        item = FeedItem(index=i)
        item.username = self._username(art)
        item.caption = self._caption(art, item.username)
        item.url = url or self._post_url(art)
        item.video = art.locator("video").count() > 0
        # Okurken sayfa kayabiliyor (görsel yüklenir, karusel boyutlanır); ekran görüntüsünden
        # hemen önce hiza son bir kez denetleniyor (ölçülen sapma: 672 piksele kadar).
        for _ in range(3):
            hiza = self._align(i, item.url)
            if hiza is None:
                break
            item.sapma = float(hiza["sapma"])
            if abs(item.sapma) <= ALIGN_TOL_PX:
                break
            self.b.page.wait_for_timeout(300)
        item.shot = self.b.shot()
        return item

    def _username(self, art) -> str:
        """Postun sahibi: ilk profil bağlantısından (/kullanici/)."""
        try:
            href = art.locator("a[href]").first.get_attribute("href", timeout=2000) or ""
        except Exception:
            return ""
        m = re.match(r"^/([^/]+)/?$", href)
        return m.group(1) if m else ""

    def _post_url(self, art) -> str:
        """Postun bağlantısı; beğenenler listesi (/liked_by/) değil."""
        links = art.locator("a[href*='/p/'], a[href*='/reel/']")
        for i in range(min(links.count(), 8)):
            href = links.nth(i).get_attribute("href") or ""
            if "liked_by" not in href and "comments" not in href:
                return href
        return ""

    def _caption(self, art, username: str) -> str:
        """Postun açıklaması (koku kaynağı).

        Gerçek sayfada açıklama, beğeni sayısı ve zaman damgasıyla aynı metin bloğunda; satırlar
        elenerek bulunuyor. Kullanıcı adı iki kez geçiyor (beğenenler satırında ve açıklamadan
        önce), ikisi de atlanıyor.
        """
        try:
            text = art.inner_text(timeout=3000)
        except Exception:
            return ""
        for line in (ln.strip() for ln in text.splitlines()):
            if not line or line == username or _COUNT_LINE.match(line) or _OTHERS_LINE.match(line):
                continue
            if line in SKIP_LINES or line.startswith(SKIP_PREFIX) or _TIME_LINE.match(line):
                continue
            if username and line.startswith(username + " "):
                line = line[len(username) + 1:].strip()  # "kullanıcı açıklama" aynı satırdaysa
            return line
        return ""

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

    def like_states(self) -> dict[str, bool]:
        """Görünen bütün postların beğeni durumu (bağlantı → beğenildi mi).

        Eylemin **yalnızca hedef postu** değiştirdiğini doğrulamak için: hesabın durumu
        günlükle uyuşmazsa bunu görmek gerekiyor (Z-44).
        """
        return self.b.page.evaluate(
            """(unlike) => {
                const out = {};
                for (const art of document.querySelectorAll('article')) {
                    // _post_url ile aynı ölçüt: beğenenler ve yorumlar bağlantısı değil.
                    const a = [...art.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
                        .find(x => !x.href.includes('liked_by') && !x.href.includes('comments'));
                    if (!a) continue;
                    const etiketler = [...art.querySelectorAll('svg[aria-label]')]
                        .map(s => s.getAttribute('aria-label'));
                    out[new URL(a.href).pathname] = etiketler.some(e => unlike.includes(e));
                }
                return out;
            }""", list(LABELS["begen"][1]))

    def act(self, action: str, text: str = "") -> dict:
        """Kararı uygular. Dönen kayıt: eylem, uygulandı mı, gerekçe."""
        self.last_frames = []  # erken dönülürse eski eylemin animasyonu gösterilmesin
        self.guard()
        try:
            self.gov.check(action, text)
        except Vetoed as e:
            return self.gov.record(action, False, f"vali: {e}")
        if self._state(action) is True:
            return self.gov.record(action, False, "zaten uygulanmış")
        if self.gov.dry_run:
            return self.gov.record(action, False, "kuru çalıştırma")
        hedef = self._post_url(self._article(self.index))
        onceki = self.like_states() if action == "begen" else None
        try:
            self._click(action, text)
        except Exception as e:  # tıklama ya da doğrulama başarısız
            return self.gov.record(action, False, f"başarısız: {type(e).__name__}: {e}")
        self.last_frames = self.grab_frames()  # eylemin animasyonu (sinek kendi kalbini görsün)
        sapma = self._stray_likes(onceki, hedef)
        if sapma:
            # Hesapta iz var ama sineğin kararı bu post değildi: sessizce geçilmemeli (Z-44).
            return self.gov.record(action, False, f"YANLIŞ POSTA DÜŞTÜ: {', '.join(sapma)}")
        ok = self._state(action)
        if action == "yorum":
            ok = True  # yorumun doğrulaması gönderimden sonra metnin listede görünmesi
        if ok is not True and action == "begen":
            # Çift dokunma tutmadı (Instagram arayüzü değişmiş olabilir): kalp düğmesine düş.
            # Animasyon çıkmaz ama beğeni kaydolur; hangi yolun kullanıldığı kayda geçer.
            try:
                icon = self._icon(action, 0)
                if icon is not None:
                    icon.click(timeout=5000)
                    self.last_frames = self.grab_frames()
                    ok = self._state(action)
            except Exception:
                ok = None
            if ok is True:
                return self.gov.record(action, True, "kalp düğmesi (çift dokunma tutmadı)")
        if ok is not True:
            return self.gov.record(action, False, "tıklandı ama durum değişmedi")
        return self.gov.record(action, True, text)

    def _stray_likes(self, onceki: dict[str, bool] | None, hedef: str) -> list[str]:
        """Hedef dışında beğeni durumu değişen postlar (Z-44)."""
        if onceki is None:
            return []
        sonraki = self.like_states()
        return [u for u, v in sonraki.items()
                if u != hedef and u in onceki and v != onceki[u]]

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
        if action == "begen" and self._double_tap(self._post_url(art)):
            return
        icon = self._icon(action, 0)
        if icon is None:
            raise RuntimeError(f"{action} düğmesi bulunamadı")
        icon.click(timeout=5000)

    _TAP_TARGET = """(el) => {
        let best = null, area = 0;
        for (const m of el.querySelectorAll('img, video')) {
            const r = m.getBoundingClientRect();
            if (r.width * r.height > area) { area = r.width * r.height; best = r; }
        }
        if (!best || area <= 10000) return null;
        const x = best.x + best.width / 2, y = best.y + best.height / 2;
        // O noktada GERÇEKTEN bu postun bir parçası duruyor mu? Sayfa kaydıysa ya da
        // üstünü bir şey örttüyse dokunuş başka posta gider (2026-09-19'da oldu).
        const hedef = document.elementFromPoint(x, y);
        return hedef && el.contains(hedef) ? {x, y} : null;
    }"""

    def _double_tap(self, url: str = "") -> bool:
        """Postun fotoğrafına çift dokunur (Instagram'ın beğeni jesti). Başardıysa True.

        Kalp düğmesine basmak yalnızca simgeyi dolduruyor; fotoğrafın üstündeki büyük kalp
        animasyonunu çift dokunma çıkarıyor ve sinek kendi beğenisini böyle görüyor (K-038'in
        yanındaki kullanıcı kararı). Çift dokunma yalnızca beğenir, beğeniyi geri almaz.

        **En büyük** görsel seçiliyor: `img` listesinin ilki post fotoğrafı değil profil
        avatarı olabiliyor ve ona dokunmak profile gider.

        **Hedef her dokunuştan hemen önce doğrulanıyor** (`elementFromPoint`). Bir kez
        doğrulamak yetmedi: gerçek oturumda sineğin 8. posta verdiği beğeni 9. posta düştü ve
        hiçbir yere kaydedilmedi — koordinat hesaplandıktan sonra sayfa kaymıştı (Z-44).
        """
        art = self._article_of(self.index, url)
        for vurus in range(2):
            kutu = art.evaluate(self._TAP_TARGET)
            if kutu is None:
                # İlk vuruş gittiyse ve ikincisi hedefi bulamıyorsa tek dokunuş kalır; tek
                # dokunuş Instagram'da beğeni değil, yani hesapta iz bırakmaz.
                return False
            self.b.page.touchscreen.tap(kutu["x"], kutu["y"])
            if vurus == 0:
                self.b.page.wait_for_timeout(DOUBLE_TAP_MS)
        return True

    @staticmethod
    def _first_visible(scope, getter):
        """Eşleşenler arasından **görünür** olanı döndürür; yoksa None.

        Sayısı saymak yetmiyor: gizli bir öğe de sayılıyor ve ona tıklamak zaman aşımına
        düşüyor. Gerçek sayfada yorum kutusu akışta hiç yok (ölçüldü: akışta 0, panelde 1)
        ama gizli bir kopya bırakan bir sürüm kodu sessizce kırardı.
        """
        loc = getter(scope)
        for i in range(min(loc.count(), 5)):
            if loc.nth(i).is_visible():
                return loc.nth(i)
        return None

    def _comment_box(self, scope):
        for ph in COMMENT_PLACEHOLDERS:
            box = self._first_visible(scope, lambda s, ph=ph: s.get_by_placeholder(ph, exact=False))
            if box is not None:
                return box
        return None

    def _comment(self, text: str) -> None:
        """Yorumu yazar ve gönderir; metin boşsa hiçbir şey yapılmaz.

        Gerçek Instagram'da (telefon görünümü) yorum kutusu akışta **yok**: yorum simgesine
        basınca /p/<kod>/comments/ adresine gidiliyor ve kutu orada. Gönder düğmesi de ancak
        **yazdıktan sonra** beliriyor (2026-09-18'de ölçüldü). Akışa dönüşü `ensure_feed`
        yapıyor: bir sonraki postta adres akışınki olmadığı için geri dönülüyor.
        """
        if not text.strip():
            raise ValueError("yorum metni boş")
        art = self._article(self.index)
        box = self._comment_box(art)
        if box is None:
            icon = self._icon("yorum", 0)
            if icon is None:
                raise RuntimeError("yorum kutusu bulunamadı")
            icon.click(timeout=5000)
            self.b.page.wait_for_timeout(1500)
            box = self._comment_box(self.b.page)
        if box is None:
            raise RuntimeError("yorum kutusu bulunamadı")
        box.click(timeout=5000)
        box.type(text, delay=120)  # insan hızında yazma; gönder düğmesi ancak yazınca beliriyor
        self.b.page.wait_for_timeout(500)
        for scope in (art, self.b.page):  # önce postun kendi düğmesi, sonra sayfadaki
            for name in POST_TEXTS:
                btn = self._first_visible(scope, lambda s, n=name: s.get_by_role("button", name=n, exact=True))
                if btn is not None:
                    btn.click(timeout=5000)
                    return
        raise RuntimeError("yorumu gönderme düğmesi bulunamadı")
