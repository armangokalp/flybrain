"""Duygu okumasının ölçeği: içerikten bağımsız referans postlarda ortalama ve std (K-036).

Motor kanallarındaki kuralın aynısı (K-016): ölçek belirli bir içeriğe verilen tepkiye göre
değil, rastgele doku + rastgele kelimelerden oluşan referans postlarla belirlenir. Böylece
"baskın duygu", sineğin o postta **her zamankinden ne kadar farklı** olduğunu gösterir.

Kullanım:
    python -m flybrain.experiments.mood_calibrate [--posts 60] [--seed 8003] [--windows 3]
"""

import argparse
import time

import numpy as np

from flybrain.motor.mood import MOODS, MoodCalibration, MoodReadout
from flybrain.motor.selector import WINDOW_MS


def measure(n_posts: int, seed: int, windows: int) -> tuple[np.ndarray, MoodReadout, float]:
    from flybrain.experiments.calibrate import CAL_SEED, make_post
    from flybrain.experiments.embodied_calibrate import _viewer

    viewer = _viewer(seed)
    mood = MoodReadout(viewer.fly.conn)
    duration = windows * WINDOW_MS
    rates = np.zeros((n_posts, len(MOODS)))
    t0 = time.perf_counter()
    for k in range(n_posts):
        viewer.observe(make_post(k, CAL_SEED), windows=windows)
        rates[k] = mood.rates(viewer.counts, duration)
        if (k + 1) % 10 == 0:
            print(f"  {k + 1}/{n_posts} post, {time.perf_counter() - t0:.0f} sn", flush=True)
    viewer.fly.eyes.close()
    viewer.fly.body.close()
    return rates, mood, duration


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--posts", type=int, default=60)
    ap.add_argument("--seed", type=int, default=8003)
    ap.add_argument("--windows", type=int, default=3)
    args = ap.parse_args()

    rates, mood, duration = measure(args.posts, args.seed, args.windows)
    cal = MoodCalibration.fit(rates, duration, mood.single_spike_rates(duration))
    path = cal.save()
    print(f"\n{'duygu':14} {'nöron':>6} {'ortalama Hz':>12} {'std':>8} {'en yüksek':>10}")
    for i, m in enumerate(MOODS):
        print(f"{m:14} {len(mood.groups[m]):6} {cal.mean[i]:12.3f} {cal.std[i]:8.3f} {rates[:, i].max():10.3f}")
    print(f"\nkalibrasyon: {path}")


if __name__ == "__main__":
    main()
