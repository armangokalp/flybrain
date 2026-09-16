"""Görsel + caption birlikte: bir postun iki bileşeni de sinekte ayırt edilebiliyor mu?

4 doğal istatistikli görsel × 4 caption = 16 post, her biri × deneme.
Okuma: inen nöron hız vektörleri, en yakın merkez sınıflandırması.
  - görsel doğruluğu (4'lü, şans %25): merkezler görsele göre
  - caption doğruluğu (4'lü, şans %25): merkezler caption'a göre
  - post doğruluğu (16'lı, şans %6)
Kararlılık: post sonrası 300 ms bekleme, ardından 200 ms'de aktif nöron sayısı.

Kullanım:
    python -m flybrain.experiments.post [--trials 3]
"""

import argparse
import json
import time

import numpy as np

from flybrain.connectome.connectome import load_connectome
from flybrain.experiments.stability import nearest_centroid_accuracy
from flybrain.experiments.vision import natural_images
from flybrain.paths import RUNS
from flybrain.senses.olfaction import OlfactoryEncoder, tokenize
from flybrain.senses.vision import VisionConfig, VisionEncoder
from flybrain.sim import BRAIN_PARAMS, Simulator

CAPTIONS = [
    "sabah kahvesi ☕ #pazartesi",
    "deniz güneş tatil 🌊",
    "kedim yine uyuyor 😴",
    "koşu antrenmanı bitti #spor",
]
VISION = VisionConfig(mode="onoff", r_max_hz=250.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()

    conn = load_connectome()
    vis = VisionEncoder(conn, VISION)
    olf = OlfactoryEncoder(conn)
    images = list(natural_images(4, seed=11).values())
    dn = conn.select(superclass="descending_neuron")

    X, img_y, cap_y, post_y, persistent, active = [], [], [], [], [], []
    t0 = time.perf_counter()
    for t in range(args.trials):
        sim = Simulator(conn, BRAIN_PARAMS, seed=300 + t, std_exempt=vis.input_neurons)
        for i, img in enumerate(images):
            for j, cap in enumerate(CAPTIONS):
                stim = vis.encode(img) + olf.encode(cap)
                sim.reset()
                r = sim.run(500, stim)
                sim.run(300)
                after = sim.run(200)
                X.append(r.rates_hz[dn])
                img_y.append(i)
                cap_y.append(j)
                post_y.append(4 * i + j)
                persistent.append(int((after.counts > 0).sum()))
                active.append(int((r.counts > 0).sum()))
    X = np.array(X)
    result = {
        "trials": args.trials,
        "vision": VISION.__dict__,
        "odors": {c: olf.activation(tokenize(c)) for c in CAPTIONS},
        "acc_image": nearest_centroid_accuracy(X, np.array(img_y)),
        "acc_caption": nearest_centroid_accuracy(X, np.array(cap_y)),
        "acc_post": nearest_centroid_accuracy(X, np.array(post_y)),
        "active_mean": float(np.mean(active)),
        "persistent_max": int(max(persistent)),
        "wall_s": time.perf_counter() - t0,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"post-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(
        f"görsel doğruluğu {result['acc_image']:.0%} (şans %25) | "
        f"caption doğruluğu {result['acc_caption']:.0%} (şans %25) | "
        f"post doğruluğu {result['acc_post']:.0%} (şans %6) | "
        f"aktif nöron ort. {result['active_mean']:.0f} | kalıcı en çok {result['persistent_max']}"
    )
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
