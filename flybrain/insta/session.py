"""Gerçek Instagram'da bir oturum: ekran → sinek → gerçek eylem (Faz 8).

Döngü, yerel oturumla (viz/session.py) aynı; yalnızca ekranın kaynağı ve eylemin gittiği yer
değişiyor:

  1. Tarayıcı postu açar, ekran görüntüsünü alır. Post videoysa (reels) kareleri toplanır ve
     sineğe simülasyon zamanıyla oynatılır (Z-37); tarayıcı kendi başına oynatmaz.
  2. Ekran görüntüsü sineğin telefonuna **solarak** gelir (K-037); postun açıklaması koku olur.
  3. Sinek 500 ms'lik pencerelerle bakar, kanallardan biri eşiği aşınca karar verir (K-016, K-032).
  4. Karar Instagram eylemiyse güvenlik valisine sorulur (K-007), sonra tarayıcı düğmeye basar ve
     sonuç doğrulanır. Kuru çalıştırmada yalnızca kaydedilir.
  5. Eylemin animasyonu sineğe oynatılır: beğeni fotoğrafa çift dokunarak yapılıyor ve sinek
     kalbin görselin üstünde büyümesini görüyor.
  6. Karar "yorum" ise metin sineğin kendisinden gelir: aday kelimeleri tek tek koklar ve
     yaklaştıklarını seçer (K-041, motor/comment.py). Yaklaştığı kelime yoksa yorum boş kalır.

Sinek **ekrana bağlıdır** (K-040): göğsü dünyada duran bir tutucuya bağlı. Korktuğunda kaçış
hareketini yapar ama gidemez; akışta ilerlemenin tek yolu kendi vereceği başka bir karardır.

Sahne: telefon dünyada duran bir nesne, sinek 2,5 mm uzakta başlıyor (K-038). Mesafeyi sineğin
kendi yürüyüşü belirliyor; kaçtığında geri çekiliyor ve postu daha geniş görüyor.

**Giriş kullanıcıya ait.** Oturum açık değilse program durur ve kullanıcıdan tarayıcıda elle giriş
yapmasını ister; şifre ne istenir ne de saklanır.

Kullanım:
    python -m flybrain.insta.session --posts 5              # kuru çalıştırma (tıklama yok)
    python -m flybrain.insta.session --posts 5 --gercek     # gerçek eylemler
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from flybrain.fly import Post
from flybrain.insta.browser import Browser
from flybrain.insta.feed import ACTION_FPS, VIDEO_FPS, InstaFeed
from flybrain.insta.governor import LOG, Governor, Limits, Stopped, report
from flybrain.insta.screen import ScreenshotFeed, Shot
from flybrain.motor.comment import CommentWriter
from flybrain.motor.selector import (
    CALIBRATION_EMBODIED_PATH,
    CALIBRATION_TETHERED_PATH,
    Calibration,
)

# Sineğin kararı → Instagram eylemi. Ötekiler (ileri, geri, sekme, tımar, ilgi kaybı) yalnızca
# gövde hareketi ve akışta ilerleme; Instagram'da karşılığı yok. "cikis" bağlı sinekte çırpınma
# olur ve postu bitirmez (K-040); yalnızca --serbest kipinde sineği akıştan çıkarır.
INSTA_ACTION = {"begen": "begen", "kaydet": "kaydet", "yorum": "yorum", "takip": "takip"}

# Yerleştirmeden sonra ilk posta geçmeden önceki bekleme. 500 ms yetmiyor: sinek ilk pencerede
# kaçıp devriliyor (kaçış 7 Hz, diklik 0,10). 2 sn'de kaçış sıfır, diklik 0,99 (docs/11-instagram.md).
SETTLE_MS = 2000.0

# Gerçek feed'de postlar arası geçiş (K-039; K-037'nin 1200 ms'ini kısaltır). Kaçırmayan en
# kısa süre aranıyor: geçiş Instagram'da olmayan bir dünya ayarı, kısası daha gerçekçi.
#
#   geçiş     deney (13 çift)   gerçek oturum (14 post)
#   anında         6/13                 6/14
#   600 ms         0/13                 1/14   ← seçilen
#   1200 ms        2/13                 1/14
#
# Ölçüm: flybrain/experiments/gecis.py (oturumun akışını taklit eder; bkz. K-039).
REAL_FADE_MS = 600.0


def _recovery_screen(fly):
    """Kaçıştan sonra toparlanma ekranı: o anki karenin ortalama parlaklığında düz gri.

    Parlaklık korunuyor çünkü ekran ışık yayan bir yüzey; karartmak ya da aydınlatmak tek
    başına bir uyaran olurdu. Kaçılan postlar zaten belirgin biçimde daha karanlık çıkıyor
    (ölçüm: parlaklık 50 vs 78), yani bu bantta oynamak sonucu kirletir.
    """
    import numpy as np

    frame = fly.feed.frame()
    return np.full_like(frame, int(round(frame.mean())))


def _video_fn(frames: list, fps: float):
    """Kare listesini `ScreenshotFeed.play`'in beklediği `video(t_ms)` biçimine çevirir.

    Video bitince None döner; son kare ekranda kalır (donmuş kare değil, videonun sonu).
    """
    def video(t_ms: float):
        k = int(t_ms / 1000.0 * fps)
        return frames[k] if 0 <= k < len(frames) else None

    return video


def _make_viewer(seed: int, homeostasis: bool = True, tether: bool = True):
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.scene import SceneConfig
    from flybrain.body.tether import TetherConfig
    from flybrain.body.viewer import FeedViewer

    class _Viewer(FeedViewer):
        pending_video = None  # reels: geçiş başladıktan sonra oynatılacak kareler

        def _screen_item(self, post: Post):
            return Shot(post.image, caption=post.caption)

        def _begin(self, post: Post):
            stim = super()._begin(post)
            if self.pending_video is not None:
                # Geçiş ekranı sıfırladığı için video ondan **sonra** başlatılıyor;
                # böylece reels solma sürerken oynamaya başlar.
                self.fly.play_video(self.pending_video)
                self.pending_video = None
            return stim

    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=SceneConfig(), seed=seed,
                      tether=TetherConfig() if tether else None)
    fly.feed = ScreenshotFeed(fly.scene.texture_shape)
    viewer = _Viewer(fly, Calibration.load(calibration_path(tether)), homeostasis=homeostasis)
    return viewer


def calibration_path(tether: bool):
    """Bağlı sineğin eşikleri ayrı dosyada (K-040): kanalların tipik düzeyi farklı."""
    if not tether:
        return CALIBRATION_EMBODIED_PATH
    if not CALIBRATION_TETHERED_PATH.exists():
        raise Stopped(f"bağlı sineğin kalibrasyonu yok ({CALIBRATION_TETHERED_PATH.name}); "
                      "önce: python -m flybrain.experiments.embodied_calibrate --bagli --save")
    return CALIBRATION_TETHERED_PATH


def _stop_if_stray(applied: dict, sira: int) -> None:
    """Eylem bakılan post dışında bir posta iz bıraktıysa oturum durur (Z-44, Z-45).

    Sonraki eylemler de aynı yanlışı büyütebilir; hesapta sineğin kararı olmayan izler birikir.
    Kayıt kapanır, günlük yazılır; neyin düştüğü `sapma` alanında.
    """
    if applied.get("sapma"):
        raise Stopped(f"post {sira}: eylem başka posta düştü ({', '.join(applied['sapma'])}); "
                      "oturum durduruldu")


def run_session(n_posts: int = 5, dry_run: bool = True, seed: int = 8003, out: str | None = None,
                headless: bool = False, limits: Limits | None = None, url: str | None = None,
                live: bool = False, fade_ms: float | None = None, tether: bool = True):
    """Oturumu yürütür. dry_run=False ise eylemler gerçekten uygulanır.

    url: gerçek Instagram yerine yerel bir sayfa (tests/sahte_akis.html). Döngünün tamamını
    gerçek hesaba dokunmadan çalıştırmak için.
    live: oturum sürerken tarayıcıdan izlenebilen canlı yayın (viz/live.py, ağır çekim).
    tether: sinek ekrana bağlı (K-040). Kaçış kararı postu bitirmez; sinek çırpınır ve
        akışta ilerlemenin tek yolu kendi vereceği başka bir karardır.
    """
    from flybrain.viz.record import SessionRecorder

    # Sahte akıştaki eylemler gerçek hesabın hız bütçesini yemesin diye ayrı bir günlüğe yazılır.
    gov = Governor(limits, log=LOG if url is None else LOG.with_name("sahte-eylemler.jsonl"), dry_run=dry_run)
    browser = Browser(headless=headless).open()
    feed = InstaFeed(browser, gov, require_login=url is None)
    viewer = None
    stream = None
    try:
        feed.open() if url is None else feed.open_url(url)
        if url is None and not browser.logged_in():
            raise Stopped("Instagram oturumu yok: açılan tarayıcıda elle giriş yap, sonra yeniden çalıştır")
        print(report(gov), flush=True)
        viewer = _make_viewer(seed, tether=tether)
        fly = viewer.fly
        writer = CommentWriter(fly, viewer.readout)  # yorumun metni (K-041)
        fly.fade_ms = REAL_FADE_MS if fade_ms is None else fade_ms  # K-039
        # Sinek akış açıkken yerleştirilir: boş (siyah) ekrandan ilk posta geçiş büyük bir
        # parlaklık değişimi ve sineği kaçırıyor (Z-25, Z-34). Gerçek kullanıcı da uygulamayı
        # zaten bir postun üstünde açar.
        first = feed.next_post()
        fly.show_post(Shot(first.shot))  # sahnedeki dokuyu da yeniler
        fly.reset()
        fly.run(SETTLE_MS)  # sinek yerine otursun
        if live:
            from flybrain.viz.live import LiveStream

            stream = LiveStream(fly)
            feed.on_frame = stream.show_browser  # kaydırma ve animasyon izleyiciye aksın
            print(f"canlı izleme: {stream.url}", flush=True)
        info = {"sinek_tohumu": seed, "post_sayisi": n_posts, "kuru_calistirma": dry_run,
                "kalibrasyon": calibration_path(tether).name, "kaynak": url or "instagram",
                "bagli": tether}
        results = []
        escapes = 0
        struggles = 0
        t0 = time.perf_counter()
        with SessionRecorder(fly, out, info=info) as rec:
            for k in range(n_posts):
                item = first if k == 0 else feed.next_post()
                if stream is not None:
                    stream.say(f"post {k + 1}/{n_posts} @{item.username}: {item.caption[:50]}")
                rec.event("instagram_post", sira=k + 1, kullanici=item.username, baglanti=item.url,
                          video=item.video)
                if item.akisa_donuldu:  # Instagram sineği akıştan çıkarmıştı (Z-38)
                    rec.event("akisa_donuldu", sira=k + 1)
                    print(f"  [{k + 1}] akıştan düşülmüştü, geri dönüldü", flush=True)
                if item.video:
                    # Reels: kareler tarayıcıdan toplanıp sineğe simülasyon zamanıyla oynatılır
                    # (Z-37). Yoksa sinek videonun tek donmuş karesini görüyordu.
                    kareler = feed.grab_video()
                    if kareler:
                        rec.event("video", sira=k + 1, kare=len(kareler), fps=VIDEO_FPS)
                        viewer.pending_video = _video_fn(kareler, VIDEO_FPS)
                def cirpinma(d, bout, _k=k, _item=item):
                    """Bağlı sinek kaçmaya kalktı ve kaçamadı (K-040)."""
                    nonlocal struggles
                    struggles += 1
                    # Kaçışın ölçüsü bağlı sinekte sıçrama kasının (TTM) kendi eklemi; göğüs
                    # yükselmesi bağlı sinekte hep sıfır (K-040, Z-43).
                    ttm = np.degrees((d.body or {}).get("ttm", 0.0))
                    rec.event("cirpinma", sira=_k + 1, nobet=bout, z=d.z.get("cikis"),
                              ttm_derece=round(ttm, 1),
                              savrulma_mm=(d.body or {}).get("gogus_savrulma_mm"))
                    msg = (f"  [{_k + 1}] kaçmaya çalıştı (nöbet {bout + 1}), bağ tuttu"
                           f" — sıçrama kası {ttm:.0f}°")
                    print(msg, flush=True)
                    if stream is not None:
                        stream.say(f"post {_k + 1}: korktu, kaçamadı (çırpınma {bout + 1})")

                decision = viewer.look(Post(image=item.shot, caption=item.caption),
                                       on_struggle=cirpinma if tether else None)
                action = INSTA_ACTION.get(decision.action)
                applied = None
                if action == "yorum":
                    # Yorumun metni: sinek aday kelimeleri tek tek kokluyor ve yaklaştıklarını
                    # seçiyor (K-041). Koklama simülasyon zamanı harcıyor; ekran değişmiyor.
                    yorum = writer.write(viewer.counts, decision.dwell_ms, item.caption)
                    rec.event("yorum_metni", sira=k + 1, metin=yorum.text, kelimeler=yorum.words,
                              skorlar={w: round(s, 3) for w, s in yorum.scores.items()})
                    if not yorum.text:
                        applied = gov.record("yorum", False, "sinek hiçbir kelimeye yaklaşmadı")
                    else:
                        applied = feed.act(action, yorum.text)
                    rec.event("instagram_eylem", sira=k + 1, eylem=action,
                              uygulandi=applied["uygulandi"], aciklama=applied["not"],
                              metin=yorum.text, sapma=applied.get("sapma", []))
                    _stop_if_stray(applied, k + 1)
                    print(f"  [{k + 1}] yorum: {yorum.text!r}"
                          + ("" if yorum.text else " (yaklaştığı kelime yok)"), flush=True)
                    if stream is not None:
                        stream.say(f"post {k + 1}: yorum → {yorum.text or '(boş)'}")
                    if feed.last_frames:
                        fly.play_video(_video_fn(feed.last_frames, ACTION_FPS))
                        fly.run(len(feed.last_frames) / ACTION_FPS * 1000.0)
                        feed.last_frames = []
                elif action is not None:
                    applied = feed.act(action)
                    rec.event("instagram_eylem", sira=k + 1, eylem=action,
                              uygulandi=applied["uygulandi"], aciklama=applied["not"],
                              sapma=applied.get("sapma", []))
                    _stop_if_stray(applied, k + 1)
                    if feed.last_frames:
                        # Sinek kendi eyleminin sonucunu görsün: beğeninin kalbi fotoğrafın
                        # üstünde büyürken ekran sineğe simülasyon zamanıyla oynatılıyor.
                        fly.play_video(_video_fn(feed.last_frames, ACTION_FPS))
                        fly.run(len(feed.last_frames) / ACTION_FPS * 1000.0)
                        feed.last_frames = []
                    else:
                        fly.feed.show(browser.screen(fly.scene.texture_shape))
                results.append((item, decision, applied))
                if stream is not None:
                    stream.say(f"post {k + 1} @{item.username} → {decision.action}"
                               + ("" if applied is None else f" ({applied['not'] or 'uygulandı'})"))
                note = "" if applied is None else f" → {action}: {'uygulandı' if applied['uygulandi'] else applied['not']}"
                print(f"post {k + 1}/{n_posts} @{item.username}: {decision.action} "
                      f"({decision.dwell_ms} ms){note} | {time.perf_counter() - t0:.0f} sn", flush=True)
                if decision.action == "cikis":
                    # Yalnızca **bağsız** sinekte olur (K-040 öncesi davranış; --serbest).
                    # Sinek uçup gitti. Yerel oturumlarda (Faz 6) bu karar akışı durdurmuyordu;
                    # deneyci sineği geri getiriyor (K-031'deki yeniden yerleştirmenin aynısı).
                    escapes += 1
                    rec.event("geri_getirildi", sira=k + 1)
                    if stream is not None:
                        stream.say(f"post {k + 1}: sinek uçtu, deneyci geri getiriyor")
                    # Toparlanırken ekranda **kaçtığı post durmuyor**. Önceden duruyordu: deneyci
                    # sineği geri getirip onu korkutan şeyin tam karşısına koyuyor, 2 saniye öyle
                    # bırakıyordu. Sinek aynı posttan tekrar tekrar kaçıyordu (kullanıcı canlı
                    # yayında gördü). Gerçek bir deneyde hayvan geri konulurken uyaran kaldırılır.
                    fly.show_post(Shot(_recovery_screen(fly)))
                    fly.reset()
                    fly.run(SETTLE_MS)
        if tether:
            print(f"bitti: {len(results)} post, {struggles} kez kaçmaya çalıştı (bağ tuttu)", flush=True)
        else:
            print(f"bitti: {len(results)} post, {escapes} kez uçup gitti (deneyci geri getirdi)", flush=True)
        return rec.path, results
    finally:
        if stream is not None:
            stream.close()
        browser.close()
        if viewer is not None:
            viewer.fly.eyes.close()
            viewer.fly.body.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--posts", type=int, default=5)
    ap.add_argument("--seed", type=int, default=8003)
    ap.add_argument("--out", default=None, help="kayıt dizini (varsayılan: runs/insta-<zaman>)")
    ap.add_argument("--gercek", action="store_true", help="eylemleri gerçekten uygula (varsayılan: kuru çalıştırma)")
    ap.add_argument("--headless", action="store_true", help="tarayıcı penceresi açılmasın (yalnızca test)")
    ap.add_argument("--sahte", action="store_true", help="gerçek Instagram yerine yerel sahte akış (tests/sahte_akis.html)")
    ap.add_argument("--izle", action="store_true", help="canlı izleme yayını aç (http://127.0.0.1:8766/)")
    ap.add_argument("--izin", default=None,
                    help="yalnızca bu eylemler uygulansın (virgülle: begen,kaydet)")
    ap.add_argument("--solma", type=float, default=None,
                    help=f"postlar arası geçiş süresi (ms; varsayılan {REAL_FADE_MS:.0f})")
    ap.add_argument("--serbest", action="store_true",
                    help="sinek bağlı olmasın (K-040 öncesi davranış: kaçınca deneyci geri getirir)")
    args = ap.parse_args()
    url = None
    if args.sahte:
        from flybrain.paths import ROOT
        url = (ROOT / "tests" / "sahte_akis.html").as_uri()
    limits = Limits.only(args.izin.split(",")) if args.izin else None
    path, _ = run_session(args.posts, dry_run=not args.gercek, seed=args.seed, out=args.out,
                          headless=args.headless, url=url, live=args.izle, fade_ms=args.solma,
                          limits=limits)
    print(f"kayıt: {path}")


if __name__ == "__main__":
    main()
