"""Model ayarlarının kararlılık, ayırt edilebilirlik ve tat doğrulaması açısından taranması.

Her ayar için:
  - Tat doğrulaması: şeker (LB3b/c) ve acı (LB1a-d) uyarımında MN9 hızı
  - Koku ayırt edilebilirliği: her biri 3 rastgele glomerülden oluşan 8 yapay
    koku; inen nöronların hız vektörüyle en yakın merkez sınıflandırması
    (birini dışarıda bırakarak). Şans düzeyi 1/8.
  - Kalıcılık: uyarım bittikten 300-500 ms sonra hâlâ ateşleyen nöron sayısı

Kullanım:
    python -m flybrain.experiments.stability [--grid finalist|temel|duyu-muaf|duyu-muaf-yuksek]
        [--workers 5] [--trials 3] [--odors 8]
Sonuçlar runs/stability-<zaman>.json dosyasına yazılır ve markdown tablo basılır.
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

import numpy as np

from flybrain.anatomy import MOTOR, SENSORY, pools
from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.paths import RUNS
from flybrain.sim import LIFParams, Simulator

STIM_HZ = 150.0
N_ODORS = 8
GLOMERULI_PER_ODOR = 3
TRIALS = 3


def make_odors(conn: Connectome, n_odors: int = N_ODORS, seed: int = 7) -> list[np.ndarray]:
    orn = pools(conn, SENSORY)["ORN"]
    types = sorted(conn.neurons.type.iloc[orn].unique())
    rng = np.random.default_rng(seed)
    return [
        conn.select(type=list(rng.choice(types, GLOMERULI_PER_ODOR, replace=False)))
        for _ in range(n_odors)
    ]


def nearest_centroid_accuracy(X: np.ndarray, y: np.ndarray) -> float:
    classes = np.unique(y)
    correct = 0
    for i in range(len(X)):
        keep = np.ones(len(X), dtype=bool)
        keep[i] = False
        cents = np.array([X[keep & (y == k)].mean(axis=0) for k in classes])
        correct += int(classes[np.argmin(((cents - X[i]) ** 2).sum(axis=1))] == y[i])
    return correct / len(X)


def trial(sim: Simulator, stim: np.ndarray, readout: np.ndarray, early_ms=200, late_ms=300):
    """Uyarım (erken + geç pencere), 300 ms bekleme, 200 ms kalıcılık ölçümü."""
    sim.reset()
    early = sim.run(early_ms, stim_idx=stim, stim_hz=STIM_HZ)
    late = sim.run(late_ms, stim_idx=stim, stim_hz=STIM_HZ)
    sim.run(300)
    after = sim.run(200)
    full_counts = early.counts + late.counts
    return {
        "early": early.rates_hz[readout],
        "full": full_counts[readout] / ((early_ms + late_ms) / 1000.0),
        "active": int((full_counts > 0).sum()),
        "persistent": int((after.counts > 0).sum()),
    }


def evaluate(conn: Connectome, params: LIFParams, trials: int = TRIALS, n_odors: int = N_ODORS) -> dict:
    S, M = pools(conn, SENSORY), pools(conn, MOTOR)
    dn = conn.select(superclass="descending_neuron")
    odors = make_odors(conn, n_odors)
    t0 = time.perf_counter()

    taste = {}
    for name in ("seker", "aci"):
        rows = [trial(Simulator(conn, params, seed=10 + t), S[name], M["hortum"]) for t in range(trials)]
        taste[name] = {
            "mn9_hz": float(np.mean([r["full"].mean() for r in rows])),
            "active": float(np.mean([r["active"] for r in rows])),
            "persistent_max": max(r["persistent"] for r in rows),
        }

    X_early, X_full, y, persistent, active = [], [], [], [], []
    for t in range(trials):
        sim = Simulator(conn, params, seed=100 + t)
        for k, odor in enumerate(odors):
            r = trial(sim, odor, dn)
            X_early.append(r["early"])
            X_full.append(r["full"])
            y.append(k)
            persistent.append(r["persistent"])
            active.append(r["active"])
    y = np.array(y)
    sim_seconds = trials * (2 + n_odors) * 1.0
    return {
        "params": asdict(params),
        "trials": trials,
        "n_odors": n_odors,
        "taste": taste,
        "odor_acc_200ms": nearest_centroid_accuracy(np.array(X_early), y),
        "odor_acc_500ms": nearest_centroid_accuracy(np.array(X_full), y),
        "odor_active": float(np.mean(active)),
        "odor_persistent_max": int(max(persistent)),
        "odor_persistent_mean": float(np.mean(persistent)),
        "wall_per_sim_second": (time.perf_counter() - t0) / sim_seconds,
    }


def grid_temel() -> list[tuple[str, LIFParams]]:
    variants = [
        ("", {}),
        ("SFA 1/400", {"adapt_mv": 1.0, "adapt_tau_ms": 400.0}),
        ("SFA 2/400", {"adapt_mv": 2.0, "adapt_tau_ms": 400.0}),
        ("STD .1/800", {"std_u": 0.1, "std_tau_ms": 800.0}),
    ]
    out = []
    for scale in (0.4, 0.45, 0.5, 0.55, 0.6):
        for label, extra in variants:
            name = f"{scale:.2f}" + (f" + {label}" if label else "")
            out.append((name, LIFParams(w_syn_mv=0.275 * scale, **extra)))
    return out


def grid_duyu_muaf() -> list[tuple[str, LIFParams]]:
    """Sinaptik depresyon, duyu nöronları muaf."""
    out = []
    for scale in (0.45, 0.5, 0.55, 0.6, 0.7):
        for u in (0.1, 0.2):
            name = f"{scale:.2f} + STD {u}/800 duyu-muaf"
            out.append((name, LIFParams(
                w_syn_mv=0.275 * scale, std_u=u, std_tau_ms=800.0, std_skip_sensory=True,
            )))
    return out


def grid_duyu_muaf_yuksek() -> list[tuple[str, LIFParams]]:
    """Daha yüksek ölçek ve daha güçlü depresyon, duyu nöronları muaf."""
    combos = [(0.7, 0.3), (0.8, 0.2), (0.8, 0.3), (1.0, 0.2), (1.0, 0.3)]
    return [
        (f"{scale:.2f} + STD {u}/800 duyu-muaf", LIFParams(
            w_syn_mv=0.275 * scale, std_u=u, std_tau_ms=800.0, std_skip_sensory=True,
        ))
        for scale, u in combos
    ]


def grid_finalist() -> list[tuple[str, LIFParams]]:
    return [
        ("A: 0.45 + STD 0.1/800", LIFParams(w_syn_mv=0.275 * 0.45, std_u=0.1, std_tau_ms=800.0)),
        ("B: 0.70 + STD 0.2/800 duyu-muaf", LIFParams(
            w_syn_mv=0.275 * 0.70, std_u=0.2, std_tau_ms=800.0, std_skip_sensory=True)),
        ("C: 0.55 + STD 0.2/800 duyu-muaf", LIFParams(
            w_syn_mv=0.275 * 0.55, std_u=0.2, std_tau_ms=800.0, std_skip_sensory=True)),
    ]


GRIDS = {
    "finalist": grid_finalist,
    "temel": grid_temel,
    "duyu-muaf": grid_duyu_muaf,
    "duyu-muaf-yuksek": grid_duyu_muaf_yuksek,
}


_CONN: Connectome | None = None


def _init_worker() -> None:
    global _CONN
    _CONN = load_connectome()


def _evaluate_named(name: str, params: LIFParams, trials: int, n_odors: int) -> dict:
    r = evaluate(_CONN, params, trials, n_odors)
    r["name"] = name
    return r


def _row(r: dict) -> str:
    t = r["taste"]
    return (
        f"| {r['name']} | {t['seker']['mn9_hz']:.1f} | {t['aci']['mn9_hz']:.1f} "
        f"| {r['odor_acc_200ms']:.0%} / {r['odor_acc_500ms']:.0%} "
        f"| {r['odor_persistent_max']} "
        f"| {max(t['seker']['persistent_max'], t['aci']['persistent_max'])} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grid", choices=GRIDS, default="temel")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--odors", type=int, default=N_ODORS)
    args = parser.parse_args()

    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"stability-{args.grid}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    configs = GRIDS[args.grid]()
    order = {name: i for i, (name, _) in enumerate(configs)}
    results = []
    with ProcessPoolExecutor(args.workers, initializer=_init_worker) as pool:
        futures = [pool.submit(_evaluate_named, name, params, args.trials, args.odors) for name, params in configs]
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            results.sort(key=lambda x: order[x["name"]])
            path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            print(f"[{len(results)}/{len(configs)}] {_row(r)}", flush=True)

    print("\n| ayar | MN9 şeker (Hz) | MN9 acı (Hz) | koku doğruluk 200 / 500 ms | kalıcı nöron (koku, en çok) | kalıcı nöron (tat, en çok) |")
    print("|---|---|---|---|---|---|")
    for r in results:
        print(_row(r))
    print(f"\nsonuçlar: {path}")


if __name__ == "__main__":
    main()
