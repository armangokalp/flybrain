"""Instagram bağlantısı: güvenlik valisi, ekran kaynağı ve tarayıcı (Faz 8)."""

import numpy as np
import pytest

from flybrain.insta.governor import Governor, Limits, Stopped, Vetoed
from flybrain.insta.screen import ScreenshotFeed, Shot


@pytest.fixture
def gov(tmp_path):
    limits = Limits(hourly={"begen": 2, "kaydet": 1, "takip": 1, "yorum": 1, "paylas": 1, "story": 1},
                    daily={"begen": 3, "kaydet": 1, "takip": 1, "yorum": 1, "paylas": 1, "story": 1},
                    gap_s=20.0, any_gap_s=5.0)
    return Governor(limits, log=tmp_path / "eylemler.jsonl", dry_run=False)


def test_governor_blocks_rate_limits_and_keeps_counts_between_sessions(gov, tmp_path):
    t = 1_000_000.0
    gov.check("begen", now=t)
    gov.record("begen", True, now=t)
    with pytest.raises(Vetoed, match="aynı eylemden"):  # aynı eylem çok erken
        gov.check("begen", now=t + 3)
    with pytest.raises(Vetoed, match="önceki eylemden"):  # başka eylem de çok erken
        gov.check("kaydet", now=t + 3)
    gov.check("begen", now=t + 30)
    gov.record("begen", True, now=t + 30)
    with pytest.raises(Vetoed, match="saatlik"):
        gov.check("begen", now=t + 60)
    gov.check("begen", now=t + 4000)  # saatlik pencere geçti
    assert gov.remaining(now=t + 60)["begen"] == (0, 1)

    tekrar = Governor(gov.limits, log=tmp_path / "eylemler.jsonl")  # sayaçlar dosyadan okunur
    assert len(tekrar.history) == 2
    with pytest.raises(Vetoed, match="saatlik"):
        tekrar.check("begen", now=t + 60)


def test_governor_vetoes_banned_words_and_logs_the_reason(gov):
    kelime = sorted(gov.banned)[0]
    with pytest.raises(Vetoed, match="yasaklı kelime"):
        gov.check("yorum", text=f"ışık {kelime} kanat")
    gov.check("yorum", text="ışık kanat şeker")  # temiz metin geçer
    kayit = gov.record("yorum", False, "vali: yasaklı kelime")
    assert kayit["uygulandi"] is False and "yasaklı" in kayit["not"]


def test_governor_stops_on_challenge_or_lost_session(gov):
    gov.watch("https://www.instagram.com/", logged_in=True)
    with pytest.raises(Stopped, match="doğrulama"):
        gov.watch("https://www.instagram.com/challenge/?next=/", logged_in=True)
    with pytest.raises(Stopped, match="oturum düştü"):
        gov.watch("https://www.instagram.com/", logged_in=False)


def test_screenshot_feed_fades_between_shots():
    shape = (60, 30)
    feed = ScreenshotFeed(shape)
    black = np.zeros((*shape, 3), np.uint8)
    white = np.full((*shape, 3), 255, np.uint8)
    feed.show(Shot(black))
    assert feed.frame().shape == (*shape, 3) and feed.frame().max() == 0
    feed.fade_to(Shot(white), now_ms=0.0, duration_ms=300.0)
    assert feed.scrolling
    feed.update(150.0)
    assert 100 < feed.frame().mean() < 160  # yarı yolda iki kare karışıyor
    feed.update(300.0)
    assert feed.frame().min() == 255 and not feed.scrolling
    assert not feed.update(400.0)  # değişiklik yoksa ekran yenilenmez


def test_screenshot_feed_fits_foreign_sizes():
    feed = ScreenshotFeed((60, 30))
    feed.show(np.full((300, 150, 3), 7, np.uint8))
    assert feed.frame().shape == (60, 30, 3) and feed.frame().mean() == 7
    with pytest.raises(NotImplementedError):
        feed.scroll_to(np.zeros((60, 30, 3), np.uint8), 0.0, 400.0)


def test_browser_opens_in_phone_size_and_dark_mode(tmp_path):
    """Tarayıcı telefon oranında, karanlık modda ve azaltılmış hareketle açılıyor (ağ yok)."""
    pytest.importorskip("playwright")
    from flybrain.body.scene import SceneConfig
    from flybrain.insta.browser import SCALE, VIEWPORT, Browser

    with Browser(profile=tmp_path / "profil", headless=True) as b:
        b.page.set_content("<style>body{background:#fff}"
                           "@media (prefers-color-scheme: dark){body{background:#000}}</style>")
        assert b.logged_in() is False
        shot = b.shot()
        # yükseklik bir piksel eksik çıkabiliyor (tarayıcının yuvarlaması)
        assert shot.shape[1] == VIEWPORT["width"] * SCALE
        assert abs(shot.shape[0] - VIEWPORT["height"] * SCALE) <= 2
        assert shot.mean() < 10  # karanlık mod
        assert b.page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
        assert b.page.evaluate("navigator.userAgent").find("iPhone") > 0
        shape = SceneConfig().texture_shape
        assert b.screen(shape).shape == (*shape, 3)


@pytest.fixture
def sahte_akis(tmp_path):
    """Yerel sahte akış sayfası: gerçek hesaba dokunmadan eylem uygulayıcıyı sınar."""
    pytest.importorskip("playwright")
    from pathlib import Path

    from flybrain.insta.browser import Browser
    from flybrain.insta.feed import InstaFeed

    page = Path(__file__).with_name("sahte_akis.html")
    gov = Governor(Limits(gap_s=0.0, any_gap_s=0.0), log=tmp_path / "eylemler.jsonl", dry_run=False)
    with Browser(profile=tmp_path / "profil", headless=True) as b:
        b.goto(page.as_uri(), wait_ms=300)
        yield InstaFeed(b, gov, require_login=False), gov, b


def test_feed_reads_posts_and_applies_actions(sahte_akis):
    feed, gov, b = sahte_akis
    item = feed.next_post()
    assert item.index == 0 and item.username == "ariflibelula"
    assert item.caption == "ışık kanat şeker sabah"  # kullanıcı adı ayıklanmış
    assert item.url == "/p/AAA111/" and item.video is False
    assert item.shot.ndim == 3 and item.shot.std() > 1

    assert feed._state("begen") is False
    kayit = feed.act("begen")
    assert kayit["uygulandi"] and feed._state("begen") is True
    assert feed.act("begen")["not"] == "zaten uygulanmış"  # iki kez beğenmez

    assert feed.act("kaydet")["uygulandi"] and feed._state("kaydet") is True
    assert feed.act("takip")["uygulandi"] and feed._state("takip") is True
    assert feed.act("yorum", text="ışık kanat")["uygulandi"]
    assert "ışık kanat" in b.page.locator("article").nth(0).locator("li.yorum").inner_text()

    ikinci = feed.next_post()  # sonraki posta geçiş, tarayıcı tarafında
    assert ikinci.index == 1 and ikinci.username == "gecekelebegi"
    assert feed._state("begen") is False  # yeni postta durum sıfır
    video = feed.read(2)
    assert video.video is True
    feed.video_time(1500.0)  # video karesi simülasyon zamanından sürülür
    assert b.page.evaluate("document.querySelector('video').paused") is True


def test_dry_run_and_veto_do_not_touch_the_page(sahte_akis):
    feed, gov, b = sahte_akis
    feed.next_post()
    gov.dry_run = True
    assert feed.act("begen")["not"] == "kuru çalıştırma"
    assert feed._state("begen") is False  # sayfaya dokunulmadı
    gov.dry_run = False
    kelime = sorted(gov.banned)[0]
    kayit = feed.act("yorum", text=f"ışık {kelime}")
    assert not kayit["uygulandi"] and "yasaklı kelime" in kayit["not"]
    assert b.page.locator("li.yorum").count() == 0
    assert [e["eylem"] for e in gov.history] == ["begen", "yorum"]  # engellenenler de kayıtta
