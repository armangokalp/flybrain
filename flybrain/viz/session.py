"""Kayıtlı oturum: gövdeli sinek telefonda akışa bakıp karar verir, her şey kaydedilir (Faz 6).

Sinek gövdeli kalibrasyonla (flybrain/motor/calibration_embodied.json) ve eşik homeostazı
açık olarak karar verir (body/viewer.py). Postlar şimdilik referans postlarla aynı üreteçten
gelir (doğal istatistikli görsel + kelime havuzundan caption); yerel feed Faz 7'de.

Kullanım:
    python -m flybrain.viz.session [--posts 30] [--seed 8003] [--out runs/oturum-<ad>]
"""

import argparse
import time

from flybrain.viz.record import SessionRecorder

POST_OFFSET = 70_000  # kalibrasyon, doğrulama ve oturum testlerinden ayrı postlar


def record_session(n_posts: int, seed: int, out: str | None = None, homeostasis: bool = True):
    from flybrain.experiments.calibrate import TEST_SEED, make_post
    from flybrain.experiments.embodied_calibrate import _viewer
    from flybrain.motor.selector import CALIBRATION_EMBODIED_PATH, Calibration

    viewer = _viewer(seed, Calibration.load(CALIBRATION_EMBODIED_PATH))
    viewer.selector.homeostasis = homeostasis
    info = {"sinek_tohumu": seed, "post_sayisi": n_posts, "post_baslangici": POST_OFFSET,
            "homeostaz": homeostasis, "kalibrasyon": CALIBRATION_EMBODIED_PATH.name}
    t0 = time.perf_counter()
    with SessionRecorder(viewer.fly, out, info=info) as rec:
        for k in range(n_posts):
            d = viewer.look(make_post(POST_OFFSET + k, TEST_SEED))
            print(f"post {k + 1}/{n_posts}: {d.action} ({d.dwell_ms} ms), "
                  f"t = {rec.now_ms / 1000:.1f} sn, {time.perf_counter() - t0:.0f} sn", flush=True)
    viewer.fly.eyes.close()
    viewer.fly.body.close()
    return rec.path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--posts", type=int, default=30)
    ap.add_argument("--seed", type=int, default=8003)
    ap.add_argument("--out")
    ap.add_argument("--no-homeostasis", action="store_true")
    args = ap.parse_args()
    path = record_session(args.posts, args.seed, args.out, not args.no_homeostasis)
    print(f"kayıt: {path}")


if __name__ == "__main__":
    main()
