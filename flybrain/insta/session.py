"""Gerçek Instagram'da bir oturum: ekran → sinek → gerçek eylem (Faz 8).

Döngü, yerel oturumla (viz/session.py) aynı; yalnızca ekranın kaynağı ve eylemin gittiği yer
değişiyor:

  1. Tarayıcı postu açar, ekran görüntüsünü alır. Videolar duraklatılır.
  2. Ekran görüntüsü sineğin telefonuna **solarak** gelir (K-030); postun açıklaması koku olur.
  3. Sinek 500 ms'lik pencerelerle bakar, kanallardan biri eşiği aşınca karar verir (K-016, K-032).
  4. Karar Instagram eylemiyse güvenlik valisine sorulur (K-007), sonra tarayıcı düğmeye basar ve
     sonuç doğrulanır. Kuru çalıştırmada yalnızca kaydedilir.
  5. Eylemden sonraki ekran görüntüsü de sineğe gösterilir: sinek kalbin kırmızıya döndüğünü görür.

**Giriş kullanıcıya ait.** Oturum açık değilse program durur ve kullanıcıdan tarayıcıda elle giriş
yapmasını ister; şifre ne istenir ne de saklanır.

Kullanım:
    python -m flybrain.insta.session --posts 5              # kuru çalıştırma (tıklama yok)
    python -m flybrain.insta.session --posts 5 --gercek     # gerçek eylemler
"""

from __future__ import annotations

import argparse
import time

from flybrain.fly import Post
from flybrain.insta.browser import Browser
from flybrain.insta.feed import InstaFeed
from flybrain.insta.governor import LOG, Governor, Limits, Stopped, report
from flybrain.insta.screen import ScreenshotFeed, Shot
from flybrain.motor.selector import CALIBRATION_EMBODIED_PATH, Calibration

# Sineğin kararı → Instagram eylemi. Ötekiler (ileri, geri, sekme, tımar, ilgi kaybı) yalnızca
# gövde hareketi ve akışta ilerleme; Instagram'da karşılığı yok. "cikis" oturumu bitirir.
INSTA_ACTION = {"begen": "begen", "kaydet": "kaydet", "yorum": "yorum", "takip": "takip"}

# Yerleştirmeden sonra ilk posta geçmeden önceki bekleme. 500 ms yetmiyor: sinek ilk pencerede
# kaçıp devriliyor (kaçış 7 Hz, diklik 0,10). 2 sn'de kaçış sıfır, diklik 0,99 (docs/11-instagram.md).
SETTLE_MS = 2000.0


def _make_viewer(seed: int, homeostasis: bool = True):
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.scene import SceneConfig
    from flybrain.body.viewer import FeedViewer

    class _Viewer(FeedViewer):
        def _screen_item(self, post: Post):
            return Shot(post.image, caption=post.caption)

    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=SceneConfig(), seed=seed)
    fly.feed = ScreenshotFeed(fly.scene.texture_shape)
    viewer = _Viewer(fly, Calibration.load(CALIBRATION_EMBODIED_PATH), homeostasis=homeostasis)
    return viewer


def run_session(n_posts: int = 5, dry_run: bool = True, seed: int = 8003, out: str | None = None,
                headless: bool = False, limits: Limits | None = None, url: str | None = None):
    """Oturumu yürütür. dry_run=False ise eylemler gerçekten uygulanır.

    url: gerçek Instagram yerine yerel bir sayfa (tests/sahte_akis.html). Döngünün tamamını
    gerçek hesaba dokunmadan çalıştırmak için.
    """
    from flybrain.viz.record import SessionRecorder

    # Sahte akıştaki eylemler gerçek hesabın hız bütçesini yemesin diye ayrı bir günlüğe yazılır.
    gov = Governor(limits, log=LOG if url is None else LOG.with_name("sahte-eylemler.jsonl"), dry_run=dry_run)
    browser = Browser(headless=headless).open()
    feed = InstaFeed(browser, gov, require_login=url is None)
    viewer = None
    try:
        feed.open() if url is None else feed.open_url(url)
        if url is None and not browser.logged_in():
            raise Stopped("Instagram oturumu yok: açılan tarayıcıda elle giriş yap, sonra yeniden çalıştır")
        print(report(gov), flush=True)
        viewer = _make_viewer(seed)
        fly = viewer.fly
        # Sinek akış açıkken yerleştirilir: boş (siyah) ekrandan ilk posta geçiş büyük bir
        # parlaklık değişimi ve sineği kaçırıyor (Z-25, Z-34). Gerçek kullanıcı da uygulamayı
        # zaten bir postun üstünde açar.
        first = feed.next_post()
        fly.show_post(Shot(first.shot))  # sahnedeki dokuyu da yeniler
        fly.reset()
        fly.run(SETTLE_MS)  # sinek yerine otursun
        info = {"sinek_tohumu": seed, "post_sayisi": n_posts, "kuru_calistirma": dry_run,
                "kalibrasyon": CALIBRATION_EMBODIED_PATH.name, "kaynak": url or "instagram"}
        results = []
        t0 = time.perf_counter()
        with SessionRecorder(fly, out, info=info) as rec:
            for k in range(n_posts):
                item = first if k == 0 else feed.next_post()
                rec.event("instagram_post", sira=k + 1, kullanici=item.username, baglanti=item.url,
                          video=item.video)
                decision = viewer.look(Post(image=item.shot, caption=item.caption))
                action = INSTA_ACTION.get(decision.action)
                applied = None
                if action == "yorum":
                    # Yorumun metni sineğin duygusundan ve kokladığı kelimelerden yazılacak (K-036).
                    applied = gov.record("yorum", False, "yorum metni üretimi henüz yok (K-036)")
                    rec.event("instagram_eylem", sira=k + 1, eylem=action, uygulandi=False,
                              aciklama=applied["not"])
                elif action is not None:
                    applied = feed.act(action)
                    rec.event("instagram_eylem", sira=k + 1, eylem=action,
                              uygulandi=applied["uygulandi"], aciklama=applied["not"])
                    fly.feed.show(browser.screen(fly.scene.texture_shape))  # eylem sonrası ekran
                results.append((item, decision, applied))
                note = "" if applied is None else f" → {action}: {'uygulandı' if applied['uygulandi'] else applied['not']}"
                print(f"post {k + 1}/{n_posts} @{item.username}: {decision.action} "
                      f"({decision.dwell_ms} ms){note} | {time.perf_counter() - t0:.0f} sn", flush=True)
                if decision.action == "cikis":
                    print("sinek oturumu bitirdi (uçup gitti)", flush=True)
                    break
        return rec.path, results
    finally:
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
    args = ap.parse_args()
    url = None
    if args.sahte:
        from flybrain.paths import ROOT
        url = (ROOT / "tests" / "sahte_akis.html").as_uri()
    path, _ = run_session(args.posts, dry_run=not args.gercek, seed=args.seed, out=args.out,
                          headless=args.headless, url=url)
    print(f"kayıt: {path}")


if __name__ == "__main__":
    main()
