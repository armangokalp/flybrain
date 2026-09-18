"""Bağlı sinekte kaçışın gövdedeki izi hangi ölçüde görünür (K-040).

Sinek ekrana bağlandığında (body/tether.py) kaçış devresi ateşlemeye devam eder ama gövde
gidemez. Sorun: "çıkış" kararı gövde onayından geçmek zorunda (K-032) ve serbest sinekteki
ölçüsü göğsün **yükselmesi** (sıçrama). Bağlı sinekte göğüs yükselemez.

İlk iki deneme ve neden yetmedikleri:

  1. *Yükselme.* Bağlı sinekte kaçış bağa karşı neredeyse tamamen yatay: yükselme 0,01 mm,
     savrulma 0,11 mm (20 ms'lik bağ). Ölçü kaçışı hiç onaylamaz.
  2. *Savrulma* (pencere içinde göğsün başlangıç noktasından en büyük uzaklığı). Ayrışmıyor:
     bağlı sinekte kaçışta 0,005–0,022 mm, dinlenirken 0,006–0,067 mm. Bağı gevşetmek de
     çözmüyor — kaçış savrulmasını artırmıyor, yalnızca dinlenmedeki salınımı büyütüyor
     (10/20/40/80 ms tarandı).

Bu deney doğru yere bakıyor: **bacaklara**. Gerçek sinekte dev lif (DNp01) TTM kasını sürer,
o da orta bacakların trokanter eklemini açar ve sinek fırlar (body/muscles.py). Bağlı sinekte
gövde gidemez ama bu hareket bacaklarda tam olarak yapılır.

Yöntem: sinek yaklaşan diske bakarken her 500 ms'lik pencerede (karar penceresiyle aynı) hem
dev lif spike'ları hem bütün gövde ölçüleri (body/confirm.MEASURES) kaydedilir. Sonra her ölçü
için sorulur: dev lifin ateşlediği pencerelerle ateşlemediği pencereleri ayırıyor mu?
Ayıran ölçü, bağlı sinekte kaçışın gövde onayı olur.

Kullanım:
    python -m flybrain.experiments.bag [--trials 8] [--seeds 11 12] [--workers 4]
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.body.confirm import MEASURES, VISIBLE_DEG, VISIBLE_MM
from flybrain.paths import RUNS

REST_MS = 2000.0     # uyarandan önce durağan ekran
WINDOW_MS = 500.0    # karar penceresi (motor/selector.WINDOW_MS ile aynı)
TETHER_TIMECONST = 0.002


def _mm(name: str) -> bool:
    return name.startswith("gogus")


def _threshold(name: str) -> float:
    return VISIBLE_MM if _mm(name) else np.radians(VISIBLE_DEG)


def _windows(fly, counter, stim_ms: float, meter, n_windows: int) -> list[dict]:
    """n_windows pencere çalıştırır; her pencerede dev lif spike'ları ve gövde ölçüleri."""
    rows = []
    for _ in range(n_windows):
        t0 = fly.brain.time_ms
        a = fly.run(WINDOW_MS, record_every_ms=5.0).arrays()
        L = np.array(counter.log)
        m = (L[:, 0] > t0) & (L[:, 0] <= fly.brain.time_ms) if len(L) else np.zeros(0, bool)
        rows.append({"t_ms": t0, "gf": int(L[m, 1].sum()) if len(L) else 0,
                     "lc4": int(L[m, 2].sum()) if len(L) else 0,
                     "olcu": meter.measure(a).tolist()})
    return rows


def _trial(tethered: bool, seed: int, post_k: int) -> list[dict]:
    from flybrain.body.confirm import BodyMeter
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.phone import PhoneFeed, fit, post_box
    from flybrain.body.scene import SceneConfig, pixel_directions
    from flybrain.body.tether import TetherConfig
    from flybrain.experiments.escape import HOLD_MS, looming_video
    from flybrain.experiments.scene import _Counter, _groups, _post

    cfg = SceneConfig()
    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=cfg, seed=seed,
                      tether=TetherConfig(timeconst_s=TETHER_TIMECONST) if tethered else None)
    counter = _Counter(fly, _groups(fly))
    meter = BodyMeter(fly.body.dofs)
    top, bottom, left, right = post_box(cfg.texture_shape)
    rows, cols = np.mgrid[top:bottom, left:right]
    dirs = pixel_directions(cfg, rows, cols)

    post = _post(post_k)
    fly.feed = PhoneFeed(cfg.texture_shape, previous=_post(100 + post_k))
    fly.show_post(post)
    fly.reset()
    counter.log.clear()

    out = []
    for r in _windows(fly, counter, 0.0, meter, int(REST_MS / WINDOW_MS)):
        out.append({**r, "evre": "dinlenme"})
    video, t_coll = looming_video(fit(post.image, right - left, bottom - top), dirs)
    fly.play_video(video)
    for r in _windows(fly, counter, 0.0, meter, int((t_coll + HOLD_MS) / WINDOW_MS) + 1):
        out.append({**r, "evre": "yaklasma"})
    for r in out:
        r.update(bagli=tethered, seed=seed, post=post_k)
    return out


def _chunk(args: tuple) -> list[dict]:
    tethered, seed, posts = args
    rows = []
    for k in posts:
        rows += _trial(tethered, seed, k)
    return rows


def _report(rows: list[dict], tethered: bool) -> None:
    sel = [r for r in rows if r["bagli"] == tethered]
    if not sel:
        return
    olcu = np.array([r["olcu"] for r in sel])
    gf = np.array([r["gf"] for r in sel])
    kacis, sakin = gf > 0, gf == 0
    print(f"\n### {'bağlı' if tethered else 'serbest'} sinek "
          f"({kacis.sum()} dev lif penceresi, {sakin.sum()} sakin pencere)")
    print(f"| ölçü | dev lif > 0 | dev lif = 0 | eşiği aşan (kaçış) | eşiği aşan (sakin) |")
    print("|---|---|---|---|---|")
    for j, name in enumerate(MEASURES):
        t = _threshold(name)
        birim = "mm" if _mm(name) else "°"
        c = 1.0 if _mm(name) else np.degrees(1.0)
        print(f"| {name} | {olcu[kacis, j].mean() * c:.3f} {birim} | {olcu[sakin, j].mean() * c:.3f} {birim} | "
              f"%{100 * (olcu[kacis, j] >= t).mean():.0f} | %{100 * (olcu[sakin, j] >= t).mean():.0f} |")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 12])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    posts = list(range(args.trials))
    jobs = [(t, s, posts) for t in (False, True) for s in args.seeds]
    rows = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for out in ex.map(_chunk, jobs):
            rows += out
            print(f"  {'bağlı' if out[0]['bagli'] else 'serbest'} tohum {out[0]['seed']} bitti "
                  f"| {time.perf_counter() - t0:.0f} sn", flush=True)

    for tethered in (False, True):
        _report(rows, tethered)
    print(f"\neşikler: göğüs {VISIBLE_MM} mm, eklem {VISIBLE_DEG}°")

    path = RUNS / f"bag-olcu-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    print(f"kayıt: {path}")


if __name__ == "__main__":
    main()
