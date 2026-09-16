"""Görme kodlayıcısı yöntemlerinin karşılaştırılması (Z-02).

Her yöntem için 8 sentetik görsel × deneme:
  gri 300 ms (taban) → görsel 500 ms (ilk 200 ms ayrıca) → gri 300 ms → gri 200 ms (dönüş)

Ölçütler:
  - Ayırt edilebilirlik: inen nöron hız vektörleriyle en yakın merkez (şans 1/8)
  - Yayılım: görsel sırasında gri tabana göre ek aktif nöron sayısı (üst sınıf bazında)
  - Dönüş: görsel sonrası aktif nöron sayısı − gri taban aktif nöron sayısı
  - Dönme asimetrisi: sol / sağ koyu dairede DNa02 (sol − sağ) hız farkı

Kullanım:
    python -m flybrain.experiments.vision [--set yontemler|onoff-hiz] [--images sentetik|dogal]
        [--workers 6] [--trials 3]
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

import numpy as np

from flybrain.anatomy import MOTOR, pools
from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.experiments.stability import nearest_centroid_accuracy
from flybrain.paths import RUNS
from flybrain.senses.vision import VisionConfig, VisionEncoder
from flybrain.sim import BRAIN_PARAMS, Simulator

H, W = 240, 480
LAYERS = ["ol_intrinsic", "visual_projection", "cb_intrinsic", "descending_neuron", "vnc_motor"]


def _disk(cx: float, cy: float, r: float, inside: float, outside: float = 0.5) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    img = np.full((H, W), outside)
    img[(xx - cx * W) ** 2 + (yy - cy * H) ** 2 < (r * H) ** 2] = inside
    return img


def test_images() -> dict[str, np.ndarray]:
    yy, xx = np.mgrid[0:H, 0:W]
    gray = {
        "koyu_daire_orta": _disk(0.5, 0.5, 0.3, 0.05),
        "acik_daire_orta": _disk(0.5, 0.5, 0.3, 0.95),
        "koyu_daire_sol": _disk(0.25, 0.5, 0.3, 0.05),
        "koyu_daire_sag": _disk(0.75, 0.5, 0.3, 0.05),
        "yatay_serit": np.where((yy // (H // 8)) % 2 == 0, 0.9, 0.1),
        "dikey_serit": np.where((xx // (W // 16)) % 2 == 0, 0.9, 0.1),
        "dama": np.where(((yy // (H // 6)) + (xx // (W // 12))) % 2 == 0, 0.9, 0.1),
        "ufuk": np.where(yy < H // 2, 0.9, 0.1),
    }
    return {k: np.repeat(v[..., None], 3, axis=2).astype(float) for k, v in gray.items()}


def natural_images(n: int = 16, seed: int = 3) -> dict[str, np.ndarray]:
    """Doğal görüntü istatistiğine sahip (1/f genlik spektrumu) renkli gürültü görselleri."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.fftfreq(W)[None, :]
    amp = 1.0 / np.maximum(np.hypot(fx, fy), 1.0 / max(H, W))
    out = {}
    for k in range(n):
        chans = []
        base = np.real(np.fft.ifft2(amp * np.exp(2j * np.pi * rng.random((H, W)))))
        for _ in range(3):
            tint = np.real(np.fft.ifft2(amp * np.exp(2j * np.pi * rng.random((H, W)))))
            ch = 0.8 * base / base.std() + 0.2 * tint / tint.std()
            chans.append(np.clip(0.5 + 0.18 * ch, 0.0, 1.0))
        out[f"dogal_{k:02d}"] = np.dstack(chans)
    return out


def natural_image(k: int, seed: int) -> np.ndarray:
    """Tek bir doğal istatistikli görsel; (seed, k) ikilisiyle bağımsız üretilir."""
    rng = np.random.default_rng([seed, k])
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.fftfreq(W)[None, :]
    amp = 1.0 / np.maximum(np.hypot(fx, fy), 1.0 / max(H, W))
    base = np.real(np.fft.ifft2(amp * np.exp(2j * np.pi * rng.random((H, W)))))
    chans = []
    for _ in range(3):
        tint = np.real(np.fft.ifft2(amp * np.exp(2j * np.pi * rng.random((H, W)))))
        ch = 0.8 * base / base.std() + 0.2 * tint / tint.std()
        chans.append(np.clip(0.5 + 0.18 * ch, 0.0, 1.0))
    return np.dstack(chans)


IMAGE_SETS = {"sentetik": test_images, "dogal": natural_images}


def configs_onoff_rate() -> list[tuple[str, VisionConfig]]:
    return [(f"onoff {r:.0f} Hz", VisionConfig(mode="onoff", r_max_hz=r)) for r in (100.0, 150.0, 250.0)]


def configs() -> list[tuple[str, VisionConfig]]:
    return [
        ("off 50 Hz", VisionConfig(mode="off", r_max_hz=50.0)),
        ("off 150 Hz", VisionConfig(mode="off", r_max_hz=150.0)),
        ("onoff 50 Hz", VisionConfig(mode="onoff", r_max_hz=50.0)),
        ("onoff 150 Hz", VisionConfig(mode="onoff", r_max_hz=150.0)),
        ("foto taban 50 Hz, tonik 9 mV", VisionConfig(mode="foto", r_base_hz=50.0, tonic_mv=9.0)),
        ("foto taban 20 Hz, tonik 12 mV", VisionConfig(mode="foto", r_base_hz=20.0, tonic_mv=12.0)),
    ]


CONFIG_SETS = {"yontemler": configs, "onoff-hiz": configs_onoff_rate}


def evaluate(conn: Connectome, cfg: VisionConfig, trials: int, image_set: str = "sentetik") -> dict:
    t0 = time.perf_counter()
    enc = VisionEncoder(conn, cfg)
    images = IMAGE_SETS[image_set]()
    stims = {k: enc.encode(v) for k, v in images.items()}
    gray = enc.gray()
    dn = conn.select(superclass="descending_neuron")
    M = pools(conn, MOTOR)
    sc = conn.neurons.superclass.to_numpy()
    layer_idx = {name: np.flatnonzero(sc == name) for name in LAYERS}

    X_early, X_full, y = [], [], []
    evoked = {name: [] for name in LAYERS}
    gray_active, back_delta, turn = [], [], {"koyu_daire_sol": [], "koyu_daire_sag": []}
    for t in range(trials):
        sim = Simulator(conn, BRAIN_PARAMS, seed=200 + t, bias_mv=enc.bias_mv, std_exempt=enc.input_neurons)
        for k, (name, stim) in enumerate(stims.items()):
            sim.reset()
            base = sim.run(300, gray)
            early = sim.run(200, stim)
            late = sim.run(300, stim)
            sim.run(300, gray)
            back = sim.run(200, gray)

            full = early.counts + late.counts
            X_early.append(early.rates_hz[dn])
            X_full.append(full[dn] / 0.5)
            y.append(k)
            base_rate = base.rates_hz
            img_rate = full / 0.5
            for layer, idx in layer_idx.items():
                evoked[layer].append(int((img_rate[idx] > base_rate[idx] + 2.0).sum()))
            gray_active.append(int((base.counts > 0).sum()))
            back_delta.append(int((back.counts > 0).sum()) - int((base.counts > 0).sum()))
            if name in turn:  # yalnızca sentetik sette
                turn[name].append(float(img_rate[M["don_sol"]].mean() - img_rate[M["don_sag"]].mean()))

    y = np.array(y)
    return {
        "config": asdict(cfg),
        "stim_neurons": {k: len(v) for k, v in stims.items()},
        "gray_stim_neurons": len(gray),
        "acc_200ms": nearest_centroid_accuracy(np.array(X_early), y),
        "acc_500ms": nearest_centroid_accuracy(np.array(X_full), y),
        "evoked_mean": {k: float(np.mean(v)) for k, v in evoked.items()},
        "layer_sizes": {k: len(v) for k, v in layer_idx.items()},
        "gray_active_mean": float(np.mean(gray_active)),
        "back_delta_max": int(np.max(back_delta)),
        "back_delta_mean": float(np.mean(back_delta)),
        "image_set": image_set,
        "n_images": len(images),
        "turn_left_disk": float(np.mean(turn["koyu_daire_sol"])) if turn["koyu_daire_sol"] else float("nan"),
        "turn_right_disk": float(np.mean(turn["koyu_daire_sag"])) if turn["koyu_daire_sag"] else float("nan"),
        "wall_s": time.perf_counter() - t0,
    }


_CONN: Connectome | None = None


def _init() -> None:
    global _CONN
    _CONN = load_connectome()


def _run(name: str, cfg: VisionConfig, trials: int, image_set: str) -> dict:
    r = evaluate(_CONN, cfg, trials, image_set)
    r["name"] = name
    return r


def _row(r: dict) -> str:
    e = r["evoked_mean"]
    return (
        f"| {r['name']} | {r['acc_200ms']:.0%} / {r['acc_500ms']:.0%} "
        f"| {e['ol_intrinsic']:.0f} | {e['visual_projection']:.0f} | {e['cb_intrinsic']:.0f} "
        f"| {e['descending_neuron']:.0f} | {e['vnc_motor']:.0f} "
        f"| {r['gray_active_mean']:.0f} | {r['back_delta_max']:+d} "
        f"| {r['turn_left_disk']:+.1f} / {r['turn_right_disk']:+.1f} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--set", choices=CONFIG_SETS, default="yontemler")
    parser.add_argument("--images", choices=IMAGE_SETS, default="sentetik")
    args = parser.parse_args()

    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"vision-{args.set}-{args.images}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    cfgs = CONFIG_SETS[args.set]()
    order = {name: i for i, (name, _) in enumerate(cfgs)}
    results = []
    with ProcessPoolExecutor(args.workers, initializer=_init) as pool:
        futures = [pool.submit(_run, name, cfg, args.trials, args.images) for name, cfg in cfgs]
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            results.sort(key=lambda x: order[x["name"]])
            path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            print(f"[{len(results)}/{len(cfgs)}] {_row(r)}", flush=True)

    print(
        f"\ngörsel seti: {args.images} ({results[0]['n_images']} görsel, şans {1 / results[0]['n_images']:.0%})"
        "\n| yöntem | doğruluk 200 / 500 ms | +OL | +VPN | +merkezi | +inen | +motor "
        "| gri taban aktif | dönüş farkı (en çok) | DNa02 sol−sağ: sol daire / sağ daire |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(_row(r))
    sizes = results[0]["layer_sizes"]
    print(f"\nkatman boyutları: {sizes}")
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
