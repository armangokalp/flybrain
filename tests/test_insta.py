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
        # Animasyonlar açık (kullanıcı kararı): sinek kendi beğenisinin kalbini görsün.
        assert not b.page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
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


def test_feed_returns_when_instagram_leaves_the_feed(sahte_akis):
    """Instagram sineği akıştan çıkarırsa geri dönülür ve bu kayda geçer (Z-38).

    İlk hizalı oturumda güvenlik uyarısı yüzünden ~3 saniye bildirim sayfası açık kaldı; kod
    fark etmediği için sinek post sandığı şeyin yerine o sayfayı gördü.
    """
    feed, _gov, b = sahte_akis
    ilk = feed.next_post()
    assert ilk.akisa_donuldu is False and feed.on_feed() is True

    b.goto("data:text/html,<h1>Notifications</h1>", wait_ms=100)
    assert feed.on_feed() is False

    ikinci = feed.next_post()
    assert ikinci.akisa_donuldu is True
    assert ikinci.username == "gecekelebegi"  # görülmüş post yeniden gösterilmez


def test_app_banner_is_closed(sahte_akis):
    """Web'e özel "Use the app" bandı kapatılır: sineğin baktığı şeridin altını örtüyordu."""
    feed, _gov, b = sahte_akis
    b.page.evaluate("""() => {
        const d = document.createElement('div');
        d.id = 'bant';
        d.innerHTML = '<div role="button">Close</div><span>Use the app</span>';
        d.querySelector('[role=button]').onclick = () => d.remove();
        document.body.appendChild(d);
    }""")
    assert feed.dismiss_app_banner() is True
    assert b.page.locator("#bant").count() == 0
    assert feed.dismiss_app_banner() is False  # yoksa dokunmaz


def test_like_uses_double_tap_on_the_photo_not_the_avatar(sahte_akis):
    """Beğeni fotoğrafa çift dokunarak yapılır (Instagram'ın kalp animasyonu böyle çıkar).

    En büyük görsel seçilmeli: `img` listesinin ilki header'daki profil avatarı ve ona çift
    dokunmak profile götürür.
    """
    feed, _gov, b = sahte_akis
    feed.next_post()
    assert feed._state("begen") is False
    assert feed._double_tap() is True
    assert feed._state("begen") is True          # fotoğraf beğenildi
    assert b.page.url.endswith("sahte_akis.html")  # avatara basılıp profile gidilmedi

    assert feed._double_tap() is True
    assert feed._state("begen") is True  # çift dokunma beğeniyi geri almaz


def test_grab_video_collects_frames_and_seeks(sahte_akis):
    """Reels'in kareleri tarayıcıdan toplanır; sinek sonra onları simülasyon zamanıyla görür.

    Gerçek kodek gerekmesin diye videonun süresi ve `currentTime`'ı sahteleniyor; sınanan şey
    döngünün kaç kare topladığı ve videoyu gerçekten sardığı.
    """
    feed, _gov, b = sahte_akis
    feed.next_post()
    feed.read(2)  # sahte akıştaki video postu
    b.page.evaluate("""() => {
        const v = document.querySelector('video');
        Object.defineProperty(v, 'duration', {get: () => 3});
        v._t = 0;
        Object.defineProperty(v, 'currentTime', {
            get() { return this._t; },
            set(x) { this._t = x; window.__sardi = (window.__sardi || []).concat(x); },
        });
    }""")
    kareler = feed.grab_video(duration_ms=400.0, fps=10.0)
    assert len(kareler) == 4 and all(k.ndim == 3 for k in kareler)
    sardi = b.page.evaluate("window.__sardi")
    assert sardi[:4] == [0.0, 0.1, 0.2, 0.3]  # kareler video zamanında ilerledi
    assert sardi[-1] == 0.0  # sonunda başa alındı


def test_grab_video_is_empty_without_a_playable_video(sahte_akis):
    """Video yoksa ya da süresi okunamıyorsa boş dönülür; donmuş kare gösterilir."""
    feed, _gov, _b = sahte_akis
    feed.next_post()  # fotoğraf postu
    assert feed.grab_video() == []


def test_action_frames_are_cleared_when_nothing_was_clicked(sahte_akis):
    """Eylem uygulanmadıysa animasyon karesi kalmaz: sinek eski eylemin sonucunu görmemeli."""
    feed, gov, _b = sahte_akis
    feed.next_post()
    assert feed.act("begen")["uygulandi"]
    assert feed.last_frames  # beğeninin animasyonu toplandı
    assert feed.act("begen")["not"] == "zaten uygulanmış"
    assert feed.last_frames == []
    gov.dry_run = True
    assert feed.act("kaydet")["not"] == "kuru çalıştırma"
    assert feed.last_frames == []


def test_transition_experiment_reads_shots_from_a_recorded_session(tmp_path):
    """Geçiş deneyi kaydedilmiş oturumdan da beslenebiliyor (tarayıcı açmadan)."""
    import json

    import imageio.v2 as iio

    from flybrain.experiments.gecis import _shots_from_run

    run = tmp_path / "oturum"
    run.mkdir()
    (run / "meta.json").write_text(json.dumps({"post_sayisi": 3}))
    with iio.get_writer(run / "ekran.mp4", fps=10, macro_block_size=1) as w:
        for k in range(30):
            w.append_data(np.full((64, 32, 3), k * 8, np.uint8))

    shots = _shots_from_run(run, 3)
    assert len(shots) == 3
    assert all(s.shape == (64, 32, 3) for s in shots)
    # Her post için farklı bir an seçilmeli, hepsi aynı kare olmamalı.
    assert len({int(s.mean()) for s in shots}) == 3


def test_zero_length_transition_switches_the_screen_at_once():
    """Geçiş süresi 0 ise ekran anında değişir (K-039): Instagram'da solma yok."""
    shape = (60, 30)
    feed = ScreenshotFeed(shape)
    feed.show(Shot(np.zeros((*shape, 3), np.uint8)))
    feed.fade_to(Shot(np.full((*shape, 3), 255, np.uint8)), now_ms=0.0, duration_ms=0.0)
    assert not feed.scrolling          # geçiş yok
    assert feed.frame().min() == 255   # yeni kare tamamen yerinde
