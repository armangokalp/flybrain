"""Eylem seçicinin kalibrasyonu ve ayrı postlarda doğrulanması (K-016, K-018).

1. Kalibrasyon: CAL_POSTS referans post (doğal istatistikli görsel + sabit
   kelime havuzundan rastgele caption). Sinek karar vermeden her posta
   MAX_WINDOWS pencere bakar; kanal hızları kaydedilir. Ortalama, standart
   sapma ve bütçe eşikleri buradan çıkarılır ve flybrain/motor/calibration.json
   dosyasına yazılır.
2. Doğrulama: kalibrasyonda kullanılmamış TEST_POSTS post, iki farklı beyin
   tohumuyla. Sinek her posta bakıp karar verir. Eylem dağılımı, beğeni/kaydet
   oranı, bakma süreleri ve iki tekrar arasındaki karar tutarlılığı raporlanır.

Referans ve test postları içerikten bağımsızdır; bu kalibrasyon sineğe bir
"zevk" öğretmez, yalnızca kanalların tipik yanıt düzeyini ölçer.

Kullanım:
    python -m flybrain.experiments.calibrate [--cal-posts 480] [--test-posts 160] [--workers 6]
    python -m flybrain.experiments.calibrate --fit-from runs/calibration-rates-<zaman>.npz
    python -m flybrain.experiments.calibrate --skip-calibration --homeostasis-test [--flies 3] [--session 240]

Ham referans hızları runs/calibration-rates-<zaman>.npz dosyasına kaydedilir;
--fit-from ile eşikler yeniden simülasyon yapmadan yeniden hesaplanabilir.
"""

import argparse
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.experiments.motor import VOCABULARY
from flybrain.experiments.vision import natural_image
from flybrain.fly import Fly, Post
from flybrain.connectome.connectome import load_connectome
from flybrain.motor.readout import CHANNELS, MotorReadout
from flybrain.motor.selector import CALIBRATION_PATH, WINDOW_MS, Calibration
from flybrain.paths import RUNS

CAL_SEED = 31
TEST_SEED = 32


def make_post(k: int, seed: int) -> Post:
    rng = np.random.default_rng([seed, k, 7])
    words = rng.choice(VOCABULARY, rng.integers(2, 7), replace=False)
    return Post(image=natural_image(k, seed), caption=" ".join(words))


def _observe_chunk(indices: list[int], fly_seed: int) -> np.ndarray:
    fly = Fly(seed=fly_seed)
    return np.stack([fly.observe(make_post(k, CAL_SEED))[0] for k in indices])


def _look_chunk(indices: list[int], fly_seed: int) -> list[dict]:
    # Sabit eşiklerle doğrulama (homeostaz kapalı): kalibrasyonun kendisini ölçer.
    fly = Fly(seed=fly_seed, calibration=Calibration.load(), homeostasis=False)
    out = []
    for k in indices:
        d = fly.look(make_post(k, TEST_SEED))
        out.append({"post": k, "action": d.action, "dwell_ms": d.dwell_ms, "z": d.z})
    return out


def _session(fly_index: int, n_posts: int) -> list[dict]:
    """Homeostaz açık bir sinek, kendine ait n_posts postu art arda izler."""
    fly = Fly(seed=3000 + fly_index, calibration=Calibration.load(), homeostasis=True)
    out = []
    for k in range(n_posts):
        d = fly.look(make_post(10_000 * (fly_index + 1) + k, TEST_SEED))
        out.append({"post": k, "action": d.action, "channel": d.channel, "dwell_ms": d.dwell_ms})
    out.append({"final_state": fly.selector.state()})
    return out


BUDGET_ROWS = [
    ("ileri", {"ileri"}), ("beğen + kaydet", {"begen", "kaydet"}), ("  kaydet", {"kaydet"}),
    ("geri", {"geri"}), ("yorum", {"yorum"}), ("takip", {"takip"}), ("çıkış", {"cikis"}),
    ("sekme", {"sekme_sol", "sekme_sag"}), ("tımar", {"timar"}), ("ilgi kaybı", {"ilgi_kaybi"}),
]
BUDGET_TARGET = {"ileri": 0.35, "beğen + kaydet": 0.15, "  kaydet": 0.02, "geri": 0.03, "yorum": 0.02,
                 "takip": 0.02, "çıkış": 0.02, "sekme": 0.05, "tımar": 0.05, "ilgi kaybı": None}


def homeostasis_test(flies: int, n_posts: int) -> None:
    t0 = time.perf_counter()
    with ProcessPoolExecutor(flies) as pool:
        sessions = list(pool.map(_session, range(flies), [n_posts] * flies))
    thirds = [(0, n_posts // 3), (n_posts // 3, 2 * n_posts // 3), (2 * n_posts // 3, n_posts)]
    print(f"\nhomeostaz testi: {flies} sinek × {n_posts} post, {time.perf_counter() - t0:.0f} sn")
    print("| eylem | bütçe | " + " | ".join(f"post {a + 1}–{b}" for a, b in thirds) + " |")
    print("|---|---|" + "---|" * len(thirds))
    for label, actions in BUDGET_ROWS:
        cells = []
        for a, b in thirds:
            acts = [r["action"] for sess in sessions for r in sess[a:b]]
            cells.append(f"%{100 * np.mean([x in actions for x in acts]):.1f}")
        target = BUDGET_TARGET[label]
        print(f"| {label} | {'–' if target is None else f'%{100 * target:.0f}'} | " + " | ".join(cells) + " |")
    likes = sum(r["action"] == "begen" for sess in sessions for r in sess[:-1])
    saves = sum(r["action"] == "kaydet" for sess in sessions for r in sess[:-1])
    print(f"hortum eylemlerinin kaydetmeye giden payı (tüm oturum): %{100 * saves / max(likes + saves, 1):.0f}")
    path = RUNS / f"homeostasis-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(sessions, ensure_ascii=False, indent=1))
    print(f"sonuçlar: {path}")


def _chunks(n: int, parts: int) -> list[list[int]]:
    return [list(map(int, c)) for c in np.array_split(np.arange(n), parts) if len(c)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cal-posts", type=int, default=480)
    parser.add_argument("--test-posts", type=int, default=160)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--skip-calibration", action="store_true")
    parser.add_argument("--fit-from", help="kaydedilmiş referans hızlarından eşikleri yeniden hesapla")
    parser.add_argument("--no-test", action="store_true")
    parser.add_argument("--homeostasis-test", action="store_true")
    parser.add_argument("--flies", type=int, default=3)
    parser.add_argument("--session", type=int, default=240)
    args = parser.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)

    if not args.skip_calibration:
        t0 = time.perf_counter()
        if args.fit_from:
            saved = np.load(args.fit_from)
            rates = saved["rates"]
            if not bool(saved.get("cumulative", False)):
                # Eski kayıt: pencere başına hızlar. Eşit uzunluktaki pencerelerin birikimli
                # hızı, pencere hızlarının ortalamasıdır. Sekme kanalında işaret kayıtlı
                # olmadığından bu bir üst sınırdır; geç pencerelerde sekme ≈ 0 olduğu için
                # fark ihmal edilebilir.
                rates = np.cumsum(rates, axis=1) / np.arange(1, rates.shape[1] + 1)[None, :, None]
                print("eski kayıt birikimli hızlara çevrildi")
        else:
            chunks = _chunks(args.cal_posts, args.workers)
            with ProcessPoolExecutor(args.workers) as pool:
                parts = list(pool.map(_observe_chunk, chunks, [1000 + i for i in range(len(chunks))]))
            rates = np.concatenate(parts)
            raw_path = RUNS / f"calibration-rates-{time.strftime('%Y%m%d-%H%M%S')}.npz"
            np.savez(raw_path, rates=rates, channels=np.array(CHANNELS), cumulative=True)
            print(f"ham referans hızları: {raw_path}")
        readout = MotorReadout(load_connectome())
        floor = np.stack([readout.single_spike_rates((w + 1) * WINDOW_MS) for w in range(rates.shape[1])])
        cal = Calibration.fit(rates, floor)
        cal.save()
        print(f"kalibrasyon: {len(rates)} post, {time.perf_counter() - t0:.0f} sn → {CALIBRATION_PATH}")
        print("| kanal | bütçe | eşik (z) | birikimli ort. Hz, 0,5 / 1 / 1,5 sn | std (tabanlı), 0,5 / 1 / 1,5 sn |")
        print("|---|---|---|---|---|")
        for j, c in enumerate(CHANNELS):
            means = " / ".join(f"{cal.mean[w][j]:.3f}" for w in range(len(cal.mean)))
            stds = " / ".join(f"{cal.std[w][j]:.3f}" for w in range(len(cal.std)))
            print(f"| {c} | %{100 * cal.budget[c]:.0f} | {cal.theta[c]:.2f} | {means} | {stds} |")
        print(f"kaydetme eşiği (z): {cal.save_theta:.2f}  (beğeni eşiği {cal.theta['hortum']:.2f})")
        print("referansta gerçekleşen oranlar:", {k: f"%{100 * v:.1f}" for k, v in cal.realized.items()})
        if cal.disabled:
            print("devre dışı kanallar:", cal.disabled)

    if args.homeostasis_test:
        homeostasis_test(args.flies, args.session)
        return
    if args.no_test:
        return
    t0 = time.perf_counter()
    chunks = _chunks(args.test_posts, args.workers)
    results = {}
    with ProcessPoolExecutor(args.workers) as pool:
        for rep in (0, 1):
            seeds = [2000 + 100 * rep + i for i in range(len(chunks))]
            results[rep] = sorted(sum(pool.map(_look_chunk, chunks, seeds), []), key=lambda r: r["post"])
    n = args.test_posts
    print(f"\ndoğrulama: {n} post × 2 tekrar, {time.perf_counter() - t0:.0f} sn")
    counts = Counter(r["action"] for rep in results.values() for r in rep)
    print("| eylem | oran |")
    print("|---|---|")
    for action, cnt in counts.most_common():
        print(f"| {action} | %{100 * cnt / (2 * n):.1f} |")
    likes, saves = counts.get("begen", 0), counts.get("kaydet", 0)
    if likes + saves:
        print(f"hortum eylemlerinin kaydetmeye giden payı: %{100 * saves / (likes + saves):.0f}")
    same = np.mean([a["action"] == b["action"] for a, b in zip(results[0], results[1])])
    print(f"iki tekrarda aynı karar: %{100 * same:.0f}")
    dwell = Counter(r["dwell_ms"] for rep in results.values() for r in rep)
    print("bakma süresi dağılımı:", {k: f"%{100 * v / (2 * n):.0f}" for k, v in sorted(dwell.items())})

    path = RUNS / f"calibrate-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps({"counts": counts, "same": same, "results": results}, ensure_ascii=False, indent=1))
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
