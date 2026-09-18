"""Postlar arası geçiş süresi: sineği kaçırmayan en kısa süre (K-030, K-037).

Instagram'da postlar arası böyle bir "solma" yok; biz koyduk çünkü ekranın bir anda değişmesi
sineği kaçırıyor (Z-25, Z-35). Geçiş dünya tarafında bir ayar: sineğin devresine dokunmuyor.
Uzun tutmak kaçışı azaltıyor ama gerçeklikten uzaklaştırıyor, o yüzden **kaçırmayan en kısa**
süre aranıyor.

Ölçüm, gerçek feed'den alınmış ardışık ekran görüntüsü çiftleriyle yapılıyor:

  1. Sinek ilk postta yerine oturur (SETTLE_MS) — **yalnızca bir kez**.
  2. Ekran, verilen sürede sıradaki posta geçer.
  3. Sinek karar verir. "cikis" (uçup gitme) = geçiş sineği kaçırdı; deneyci geri getirir
     ve akış sürer, tıpkı gerçek oturumdaki gibi.

Aynı post dizisi her sürede kullanılıyor, yani süreler arasındaki fark içerikten gelmiyor.

**Protokol neden böyle:** İlk sürüm her çiftten önce sineği sıfırlıyordu; her deneme dinlenmiş
bir sinekle başlıyor ve geçişin etkisi görünmüyordu. O ölçüm "geçiş gereksiz" dedi, geçişsiz
gerçek oturum 14 postta 6 kaçış verdi (1200 ms ile 1). Ölçüm, ölçtüğü şeyin kullanıldığı
koşulu taklit etmeli.

**Neden yeniden ölçülüyor:** Eşik değerleri ve sahnenin geometrisi değiştikçe sonuç değişiyor.
K-037'nin 1200 ms'i ekranın sineğin başını izlediği düzende ölçülmüştü (K-038 öncesi).

Gerçek hesaba yalnızca **okuma** için dokunulur; hiçbir eylem uygulanmaz.

Kullanım:
    python -m flybrain.experiments.gecis [--postlar 10] [--sureler 0,300,600,1200] [--seed 8003]
    python -m flybrain.experiments.gecis --kayittan runs/insta-k038   # tarayıcı açmadan
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from flybrain.paths import RUNS

SETTLE_MS = 2000.0  # insta/session.py ile aynı
VARSAYILAN_SURELER = (0.0, 300.0, 600.0, 1200.0)


def _shots_from_feed(n: int) -> list[np.ndarray]:
    """Gerçek akıştan n ekran görüntüsü (yalnızca okuma; hiçbir eylem uygulanmaz)."""
    from flybrain.insta.browser import Browser
    from flybrain.insta.feed import InstaFeed
    from flybrain.insta.governor import Governor, Limits

    b = Browser(headless=True).open()
    try:
        feed = InstaFeed(b, Governor(Limits.only([])))  # hiçbir eyleme izin yok
        feed.open()
        shots = []
        for k in range(n):
            item = feed.next_post()
            shots.append(item.shot)
            print(f"  {k + 1}/{n} @{item.username}", flush=True)
        return shots
    finally:
        b.close()


def _shots_from_run(path: Path, n: int) -> list[np.ndarray]:
    """Kaydedilmiş bir oturumun ekran videosundan kareler (tarayıcı açılmaz)."""
    import imageio.v2 as iio

    meta = json.loads((path / "meta.json").read_text())
    kareler = [f for f in iio.get_reader(path / "ekran.mp4")]
    # Her postun ortasından bir kare: geçişlerin arasında, ekran durulmuşken.
    adim = len(kareler) / max(1, meta.get("post_sayisi", n))
    return [kareler[min(len(kareler) - 1, int((k + 0.5) * adim))] for k in range(n)]


def run(shots: list[np.ndarray], sureler, seed: int) -> dict:
    from flybrain.experiments.scene import _Counter, _groups
    from flybrain.fly import Post
    from flybrain.insta.screen import Shot
    from flybrain.insta.session import _make_viewer

    viewer = _make_viewer(seed, homeostasis=False)
    fly = viewer.fly
    counter = _Counter(fly, _groups(fly))
    sonuc = {}
    try:
        for sure in sureler:
            # **Oturumun akışı taklit ediliyor**: sinek yalnızca başta ve kaçıştan sonra
            # sıfırlanır, geçişler arka arkaya gelir. İlk sürümde her çiftten önce sıfırlama
            # vardı; her deneme dinlenmiş bir sinekle başlıyordu ve geçişin etkisi ölçülemiyordu.
            # O ölçüm "geçiş gereksiz" dedi, gerçek oturum 14 postta 6 kaçış verdi (K-039).
            fly.show_post(Shot(shots[0]))
            fly.reset()
            fly.run(SETTLE_MS)
            fly.fade_ms = sure
            kacis, pencereler, dev_lif, eylemler = 0, [], 0, []
            for b in shots[1:]:
                t0 = fly.brain.time_ms
                counter.log.clear()
                karar = viewer.look(Post(image=b, caption=""))
                w = counter.window(t0, fly.brain.time_ms)
                dev_lif += w.get("dev_lif", 0)
                eylemler.append(karar.action)
                if karar.action == "cikis":
                    kacis += 1
                    pencereler.append(karar.window)
                    fly.reset()  # deneyci sineği geri getiriyor (oturumdaki gibi)
                    fly.run(SETTLE_MS)
            sonuc[sure] = {"kacis": kacis, "cift": len(shots) - 1, "dev_lif": dev_lif,
                           "pencereler": pencereler, "eylemler": eylemler}
            print(f"  {sure:6.0f} ms: kaçış {kacis}/{len(shots) - 1}, dev lif {dev_lif}", flush=True)
    finally:
        fly.eyes.close()
        fly.body.close()
    return sonuc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--postlar", type=int, default=10)
    ap.add_argument("--sureler", default=",".join(f"{s:g}" for s in VARSAYILAN_SURELER))
    ap.add_argument("--seed", type=int, default=8003)
    ap.add_argument("--kayittan", help="gerçek feed yerine kaydedilmiş oturumun ekran videosu")
    args = ap.parse_args()
    sureler = [float(s) for s in args.sureler.split(",")]

    print(f"ekran görüntüleri ({args.postlar}):", flush=True)
    shots = (_shots_from_run(Path(args.kayittan), args.postlar) if args.kayittan
             else _shots_from_feed(args.postlar))
    print(f"\n{len(shots) - 1} ardışık çift, {len(sureler)} süre:", flush=True)
    sonuc = run(shots, sureler, args.seed)

    print(f"\n| geçiş | kaçış | dev lif spike |")
    print("|---|---|---|")
    for sure, r in sonuc.items():
        etiket = "anında" if sure == 0 else f"{sure:.0f} ms"
        print(f"| {etiket} | {r['kacis']}/{r['cift']} | {r['dev_lif']} |")

    out = RUNS / f"gecis-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"seed": args.seed, "kaynak": args.kayittan or "instagram",
                               "sonuc": {str(k): v for k, v in sonuc.items()}},
                              ensure_ascii=False, indent=1))
    print(f"\nkayıt: {out}")


if __name__ == "__main__":
    main()
