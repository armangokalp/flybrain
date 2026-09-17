"""Gövdeli sinekte eylem seçicinin kalibrasyonu, gövde onayı ve doğrulama (K-016, K-020, K-031, K-032).

Faz 4'teki kalibrasyon (experiments/calibrate.py) gövdesiz sinek içindi: durağan görme
kodlaması, 250 Hz. Gövdeli sinekte görme zamansaldır (K-027, 125 Hz), propriyosepsiyon
açıktır, postlar telefon ekranında solarak değişir (K-030). Kanalların tipik düzeyi bu
yüzden farklıdır ve eşikler yeniden çıkarılır.

1. Kayıt: her işçi bir sinek. Sinek referans postlara (calibrate.make_post, CAL_SEED) art
   arda karar vermeden bakar (body/viewer.FeedViewer.observe). Beyin ve gövde postlar
   arasında sıfırlanmaz; düşen sineği deneyci yeniden yerleştirir (K-031). Her pencerede
   kanalların birikimli hızları, baş çevirme yönü, gövde ölçüleri (body/confirm.py),
   en düşük diklik ve yerleştirme sayısı kaydedilir.
2. Eşikler: karar kuralı gövde onayıyla (K-032) uygulanarak bütçeye göre çıkarılır ve
   flybrain/motor/calibration_embodied.json dosyasına yazılır (--save).
   Rapor, onaysız kuralda her kararın gövdede görünür olup olmadığını da gösterir.
3. Doğrulama (--test-posts): kalibrasyonda kullanılmamış postlar, iki farklı beyin tohumuyla.
   Sinek her posta bakıp karar verir (FeedViewer.look, homeostaz kapalı).
4. Oturum (--session N): homeostaz açık sinekler N postu art arda izler; eylem oranlarının
   oturum boyunca bütçeye yaklaşıp yaklaşmadığı ölçülür.

Kullanım:
    python -m flybrain.experiments.embodied_calibrate [--posts 480] [--workers 6] [--save] [--test-posts 120]
    python -m flybrain.experiments.embodied_calibrate --fit-from runs/embodied-cal-<zaman>.npz [--save] [--test-posts 120]
    python -m flybrain.experiments.embodied_calibrate --fit-from runs/embodied-cal-<zaman>.npz --session 150 --flies 3
"""

import argparse
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.body.confirm import CHANNEL_MEASURE, MEASURES, VISIBLE_DEG, VISIBLE_MM, visible
from flybrain.body.embodied import UPRIGHT_MIN
from flybrain.motor.readout import CHANNELS
from flybrain.motor.selector import CALIBRATION_EMBODIED_PATH, WINDOW_MS, Calibration, _simulate
from flybrain.paths import RUNS


def _viewer(fly_seed: int, calibration: Calibration | None = None):
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.phone import FeedPost
    from flybrain.body.scene import SceneConfig
    from flybrain.body.viewer import FeedViewer
    from flybrain.experiments.calibrate import CAL_SEED, make_post

    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=SceneConfig(), seed=fly_seed)
    viewer = FeedViewer(fly, calibration, homeostasis=False)
    fly.show_post(FeedPost(make_post(100_000 + fly_seed, CAL_SEED).image))
    fly.reset()
    fly.run(WINDOW_MS)
    return viewer


def observe_chunk(indices: list[int], fly_seed: int) -> dict[str, np.ndarray]:
    from flybrain.experiments.calibrate import CAL_SEED, make_post

    viewer = _viewer(fly_seed)
    obs = [viewer.observe(make_post(k, CAL_SEED)) for k in indices]
    return {
        "posts": np.array(indices),
        "rates": np.stack([o.rates for o in obs]),
        "turns": np.stack([o.turns for o in obs]),
        "body": np.stack([o.measures for o in obs]),
        "upright": np.stack([o.upright for o in obs]),
        "placed": np.stack([o.repositions for o in obs]),
        "fly": np.full(len(indices), fly_seed),
    }


def look_chunk(indices: list[int], fly_seed: int, calibration: dict, homeostasis: bool = False) -> list[dict]:
    from flybrain.experiments.calibrate import TEST_SEED, make_post

    viewer = _viewer(fly_seed, Calibration(**calibration))
    viewer.selector.homeostasis = homeostasis
    out = []
    for k in indices:
        d = viewer.look(make_post(k, TEST_SEED))
        out.append({"post": k, "eylem": d.action, "kanal": d.channel, "sure_ms": d.dwell_ms, "govde": d.body})
    return out


def _chunks(n: int, parts: int) -> list[list[int]]:
    return [list(map(int, c)) for c in np.array_split(np.arange(n), parts) if len(c)]


def record(n_posts: int, workers: int) -> str:
    t0 = time.perf_counter()
    chunks = _chunks(n_posts, workers)
    with ProcessPoolExecutor(workers) as pool:
        parts = list(pool.map(observe_chunk, chunks, [5000 + i for i in range(len(chunks))]))
    data = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    path = RUNS / f"embodied-cal-{time.strftime('%Y%m%d-%H%M%S')}.npz"
    np.savez(path, channels=np.array(CHANNELS), body_names=np.array(MEASURES), **data)
    print(f"kayıt: {n_posts} post, {workers} sinek, {time.perf_counter() - t0:.0f} sn → {path}")
    return str(path)


def fit(data: dict, confirmed: bool) -> Calibration:
    from flybrain.connectome.connectome import load_connectome
    from flybrain.motor.readout import MotorReadout

    rates = data["rates"]
    readout = MotorReadout(load_connectome())
    floor = np.stack([readout.single_spike_rates((w + 1) * WINDOW_MS) for w in range(rates.shape[1])])
    return Calibration.fit(rates, floor, visible(data["body"]) if confirmed else None)


def decisions(cal: Calibration, rates: np.ndarray, vis: np.ndarray | None = None):
    """Karar kuralını kayda uygular: (karar penceresi, kanal; −1 ilgi kaybı)."""
    Z = (rates - np.array(cal.mean)) / np.array(cal.std)
    theta = np.array([cal.theta[c] for c in CHANNELS])
    enabled = np.array([c not in cal.disabled for c in CHANNELS])
    active = rates > 0 if vis is None else (rates > 0) & vis
    first, winner, _ = _simulate(Z, theta, enabled, active)
    return first, winner


def consistency(data: dict, cal: Calibration) -> dict:
    """Onaysız kuralın kararlarında ilgili bölge görünür hareket etti mi."""
    first, winner = decisions(cal, data["rates"])
    vis = visible(data["body"])
    out = {}
    for j, ch in enumerate(CHANNELS):
        sel = np.flatnonzero(winner == j)
        out[ch] = {"karar": int(len(sel)), "olcu": CHANNEL_MEASURE[ch],
                   "gorunur": float(vis[sel, first[sel], j].mean()) if len(sel) else None}
    return out


def report(data: dict, cal: Calibration, plain: Calibration) -> dict:
    print(f"\n{len(data['rates'])} post; dikliği {UPRIGHT_MIN}'in altına inen pencere: "
          f"%{100 * (data['upright'] < UPRIGHT_MIN).mean():.1f}; yeniden yerleştirme: {int(data['placed'].sum())} "
          f"(postların %{100 * (data['placed'].sum(axis=1) > 0).mean():.1f}'inde)")
    print(f"gövde onayı: eklemlerde ≥ {VISIBLE_DEG}°, göğüste ≥ {VISIBLE_MM} mm")
    print("| kanal | bütçe | eşik (z) | birikimli ort. Hz 0,5 / 1 / 1,5 sn | std | sıfır olmayan post |")
    print("|---|---|---|---|---|---|")
    rates = data["rates"]
    for j, c in enumerate(CHANNELS):
        means = " / ".join(f"{cal.mean[w][j]:.3f}" for w in range(len(cal.mean)))
        stds = " / ".join(f"{cal.std[w][j]:.3f}" for w in range(len(cal.std)))
        print(f"| {c} | %{100 * cal.budget[c]:.0f} | {cal.theta[c]:.2f} | {means} | {stds} | "
              f"%{100 * (np.abs(rates[:, -1, j]) > 0).mean():.0f} |")
    print(f"kaydetme eşiği (z): {cal.save_theta:.2f} (beğeni {cal.theta['hortum']:.2f})")
    print("gerçekleşen oranlar (onaylı):", {k: f"%{100 * v:.1f}" for k, v in cal.realized.items()})
    print("gerçekleşen oranlar (onaysız):", {k: f"%{100 * v:.1f}" for k, v in plain.realized.items()})
    cons = consistency(data, plain)
    print("onaysız kuralda görünür hareketli karar:",
          {c: (f"%{100 * r['gorunur']:.0f} / {r['karar']}" if r["karar"] else "–") for c, r in cons.items()})
    return cons


def validate(cal: Calibration, n_posts: int, workers: int) -> dict:
    t0 = time.perf_counter()
    chunks = _chunks(n_posts, workers)
    results = {}
    with ProcessPoolExecutor(workers) as pool:
        for rep in (0, 1):
            seeds = [7000 + 100 * rep + i for i in range(len(chunks))]
            parts = pool.map(look_chunk, chunks, seeds, [cal.__dict__] * len(chunks))
            results[rep] = sorted(sum(parts, []), key=lambda r: r["post"])
    rows = [r for rep in results.values() for r in rep]
    counts = Counter(r["eylem"] for r in rows)
    print(f"\ndoğrulama: {n_posts} post × 2 tekrar, {time.perf_counter() - t0:.0f} sn")
    print("| eylem | oran |")
    print("|---|---|")
    for action, cnt in counts.most_common():
        print(f"| {action} | %{100 * cnt / len(rows):.1f} |")
    same = float(np.mean([a["eylem"] == b["eylem"] for a, b in zip(results[0], results[1])]))
    placed = sum(r["govde"]["yeniden_yerlestirme"] for r in rows)
    dwell = {k: f"%{100 * v / len(rows):.0f}" for k, v in sorted(Counter(r["sure_ms"] for r in rows).items())}
    print(f"iki tekrarda aynı karar: %{100 * same:.0f}; bakma süresi: {dwell}; yeniden yerleştirme: {placed}")
    return {"sayilar": dict(counts), "ayni_karar": same, "sonuclar": results}


BUDGET_ROWS = [
    ("ileri", {"ileri"}), ("beğen + kaydet", {"begen", "kaydet"}), ("  kaydet", {"kaydet"}),
    ("geri", {"geri"}), ("yorum", {"yorum"}), ("takip", {"takip"}), ("çıkış", {"cikis"}),
    ("sekme", {"sekme_sol", "sekme_sag"}), ("tımar", {"timar"}), ("ilgi kaybı", {"ilgi_kaybi"}),
]
BUDGET_TARGET = {"ileri": 0.35, "beğen + kaydet": 0.15, "  kaydet": 0.02, "geri": 0.03, "yorum": 0.02,
                 "takip": 0.02, "çıkış": 0.02, "sekme": 0.05, "tımar": 0.05, "ilgi kaybı": None}


def session(cal: Calibration, flies: int, n_posts: int) -> dict:
    """Homeostaz açık sinekler, kendilerine ait n_posts postu art arda izler."""
    t0 = time.perf_counter()
    indices = [[10_000 * (i + 1) + k for k in range(n_posts)] for i in range(flies)]
    with ProcessPoolExecutor(flies) as pool:
        sessions = list(pool.map(look_chunk, indices, [8000 + i for i in range(flies)],
                                 [cal.__dict__] * flies, [True] * flies))
    thirds = [(0, n_posts // 3), (n_posts // 3, 2 * n_posts // 3), (2 * n_posts // 3, n_posts)]
    print(f"\noturum: {flies} sinek × {n_posts} post (homeostaz açık), {time.perf_counter() - t0:.0f} sn")
    print("| eylem | bütçe | " + " | ".join(f"post {a + 1}–{b}" for a, b in thirds) + " |")
    print("|---|---|" + "---|" * len(thirds))
    for label, actions in BUDGET_ROWS:
        cells = [f"%{100 * np.mean([r['eylem'] in actions for sess in sessions for r in sess[a:b]]):.1f}"
                 for a, b in thirds]
        target = BUDGET_TARGET[label]
        print(f"| {label} | {'–' if target is None else f'%{100 * target:.0f}'} | " + " | ".join(cells) + " |")
    placed = sum(r["govde"]["yeniden_yerlestirme"] for sess in sessions for r in sess)
    print(f"yeniden yerleştirme: {placed}")
    return {"oturumlar": sessions}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--posts", type=int, default=480)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--fit-from", help="kayıttan eşikleri yeniden hesapla")
    ap.add_argument("--save", action="store_true", help=f"eşikleri {CALIBRATION_EMBODIED_PATH.name} dosyasına yaz")
    ap.add_argument("--test-posts", type=int, default=0, help="doğrulama postu sayısı (0: doğrulama yok)")
    ap.add_argument("--session", type=int, default=0, help="homeostaz oturumunda sinek başına post (0: yok)")
    ap.add_argument("--flies", type=int, default=3)
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    path = args.fit_from or record(args.posts, args.workers)
    data = dict(np.load(path))
    cal, plain = fit(data, confirmed=True), fit(data, confirmed=False)
    out = {"kayit": path, "kalibrasyon": cal.__dict__, "uyum_onaysiz": report(data, cal, plain)}
    if args.save:
        cal.save(CALIBRATION_EMBODIED_PATH)
        print(f"kalibrasyon kaydedildi: {CALIBRATION_EMBODIED_PATH}")
    if args.test_posts:
        out["dogrulama"] = validate(cal, args.test_posts, args.workers)
    if args.session:
        out["oturum"] = session(cal, args.flies, args.session)
    rapor = RUNS / f"embodied-cal-rapor-{time.strftime('%Y%m%d-%H%M%S')}.json"
    rapor.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float))
    print(f"rapor: {rapor}")


if __name__ == "__main__":
    main()
