"""Motor havuzlarının gerçekçi postlara ve özel sondalara yanıtı (Faz 4).

Referans kümesi: doğal istatistikli görseller + sabit bir kelime havuzundan
rastgele caption'lar. Her uyarım için birden çok deneme; her denemede 1000 ms
boyunca tüm çıkış nöronlarının (inen nöronlar, beyin ve omurilik motor nöronları,
motor havuzları) spike sayıları 50 ms'lik dilimlerle kaydedilir. Böylece farklı
okuma kuralları yeniden simülasyon yapmadan karşılaştırılabilir.

Kullanım:
    python -m flybrain.experiments.motor [--posts 32] [--trials 2] [--workers 4]
Ham veriler runs/motor-<zaman>.npz dosyasına yazılır ve özet tablo basılır.
"""

import argparse
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.anatomy import MOTOR, SENSORY, pools
from flybrain.connectome.connectome import load_connectome
from flybrain.experiments.post import VISION
from flybrain.experiments.vision import natural_images
from flybrain.paths import RUNS
from flybrain.senses.olfaction import OlfactoryEncoder
from flybrain.senses.reward import RewardEncoder
from flybrain.senses.vision import VisionEncoder
from flybrain.sim import BRAIN_PARAMS, Simulator, Stimulus

BIN_MS = 50
DURATION_MS = 1000
POOL_NAMES = list(MOTOR)
IMAGE_SEED = 21

# İçerikten bağımsız, sabit bir kelime havuzu (Türkçe, İngilizce, emoji).
VOCABULARY = (
    "sabah kahve gün güneş deniz tatil yaz kış yağmur kedi köpek aile arkadaş sevgi "
    "mutlu yorgun hafta sonu akşam yemek tatlı pizza spor koşu yoga kitap müzik konser "
    "şehir yol doğa orman dağ gece yıldız ay moda stil yeni ürün indirim iş toplantı "
    "love life happy summer travel food coffee friends weekend vibes art photo "
    "☕ 🌊 😴 ❤️ 🔥 ✨ 🌙 🍕 🐶 🐱"
).split()

PROBES = ["gri", "seker", "aci", "odul", "yalniz_koku"]


def captions(n: int, seed: int = 5) -> list[str]:
    rng = np.random.default_rng(seed)
    return [" ".join(rng.choice(VOCABULARY, rng.integers(2, 7), replace=False)) for _ in range(n)]


class _Worker:
    """Her süreçte bir kez kurulan konnektom, kodlayıcılar ve görseller."""

    def __init__(self, n_posts: int):
        self.conn = load_connectome()
        self.vis = VisionEncoder(self.conn, VISION)
        self.olf = OlfactoryEncoder(self.conn)
        self.pools = pools(self.conn, MOTOR)
        self.outputs = output_neurons(self.conn)
        self.images = list(natural_images(n_posts, seed=IMAGE_SEED).values())
        self.captions = captions(n_posts)
        S = pools(self.conn, SENSORY)
        self.probes = {
            "gri": Stimulus.empty(),
            "seker": Stimulus.of(S["seker"], 150.0),
            "aci": Stimulus.of(S["aci"], 150.0),
            "odul": RewardEncoder(self.conn).encode(rewards=20),
            "yalniz_koku": self.olf.encode("sabah kahve deniz"),
        }

    def stimulus(self, kind: str, key) -> Stimulus:
        if kind == "post":
            return self.vis.encode(self.images[key]) + self.olf.encode(self.captions[key])
        return self.probes[key]

    def run(self, kind: str, key, seed: int) -> np.ndarray:
        stim = self.stimulus(kind, key)
        sim = Simulator(self.conn, BRAIN_PARAMS, seed=seed, std_exempt=self.vis.input_neurons)
        out = np.zeros((DURATION_MS // BIN_MS, len(self.outputs)), dtype=np.int16)
        for b in range(DURATION_MS // BIN_MS):
            out[b] = sim.run(BIN_MS, stim).counts[self.outputs]
        return out


_W: _Worker | None = None


def _init(n_posts: int) -> None:
    global _W
    _W = _Worker(n_posts)


def output_neurons(conn) -> np.ndarray:
    """Kaydedilen nöronlar: inen nöronlar, motor nöronlar ve motor havuzlarının üyeleri."""
    sc = conn.neurons.superclass.fillna("")
    base = np.flatnonzero(sc.isin(["descending_neuron", "vnc_motor", "cb_motor"]).to_numpy())
    extra = np.concatenate(list(pools(conn, MOTOR).values()))
    return np.unique(np.r_[base, extra])


def _job(kind: str, key, seed: int):
    return kind, key, seed, _W.run(kind, key, seed)


def summarize(path) -> None:
    d = np.load(path, allow_pickle=True)
    kinds, keys, out = d["kinds"], d["keys"], d["out"]
    conn = load_connectome()
    outputs = d["outputs"]
    pos = {n: i for i, n in enumerate(outputs)}
    M = pools(conn, MOTOR)
    bins = np.stack([out[:, :, [pos[n] for n in M[k]]].sum(axis=2) for k in POOL_NAMES], axis=2)
    sizes = np.array([len(M[k]) for k in POOL_NAMES])
    dn_cols = np.flatnonzero(conn.neurons.superclass.to_numpy()[outputs] == "descending_neuron")
    dn_total = out[:, :, dn_cols].sum(axis=1)
    total = bins.sum(axis=1)                       # deneme × havuz (1 sn'deki spike)
    rate = total / sizes                            # nöron başına Hz
    post = kinds == "post"
    first = np.where(bins > 0, np.arange(bins.shape[1])[None, :, None], 10**6).min(axis=1) * BIN_MS

    print("\nGerçekçi postlar (nöron başına Hz; 'ateşleyen' = en az bir spike):")
    print("| havuz | nöron | ateşleyen deneme | ort. Hz | en çok Hz | ilk spike medyanı (ms) | denemeler arası tutarlılık (r) |")
    print("|---|---|---|---|---|---|---|")
    trials = d["trials"].item()
    for j, name in enumerate(POOL_NAMES):
        x = rate[post, j]
        fired = total[post, j] > 0
        lat = first[post, j][fired]
        # aynı postun iki denemesi arasındaki korelasyon (post başına ortalama hız)
        per_post = x.reshape(-1, trials)
        r = np.corrcoef(per_post[:, 0], per_post[:, 1])[0, 1] if trials > 1 and per_post[:, 0].std() > 0 and per_post[:, 1].std() > 0 else float("nan")
        print(f"| {name} | {sizes[j]} | %{100 * fired.mean():.0f} | {x.mean():.1f} | {x.max():.1f} "
              f"| {np.median(lat) if len(lat) else float('nan'):.0f} | {r:.2f} |")

    print("\nÖzel sondalar (nöron başına Hz, denemelerin ortalaması):")
    print("| sonda | " + " | ".join(POOL_NAMES) + " | aktif inen nöron |")
    print("|---|" + "---|" * (len(POOL_NAMES) + 1))
    for probe in PROBES:
        m = (kinds == "probe") & (keys == probe)
        vals = rate[m].mean(axis=0)
        dn_active = (dn_total[m] > 0).sum(axis=1).mean()
        print(f"| {probe} | " + " | ".join(f"{v:.1f}" for v in vals) + f" | {dn_active:.0f} |")
    dn_post = (dn_total[post] > 0).sum(axis=1)
    print(f"\nPostlarda aktif inen nöron sayısı: ortalama {dn_post.mean():.0f}, en az {dn_post.min()}, en çok {dn_post.max()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--posts", type=int, default=32)
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--summarize", help="var olan bir .npz dosyasını özetle")
    args = parser.parse_args()
    if args.summarize:
        summarize(args.summarize)
        return

    jobs = [("post", i, 500 + t) for i in range(args.posts) for t in range(args.trials)]
    jobs += [("probe", p, 500 + t) for p in PROBES for t in range(args.trials)]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.posts,)) as pool:
        out = list(pool.map(_job, *zip(*jobs), chunksize=4))
    conn = load_connectome()
    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"motor-{time.strftime('%Y%m%d-%H%M%S')}.npz"
    np.savez(
        path,
        kinds=np.array([o[0] for o in out]),
        keys=np.array([str(o[1]) for o in out]),
        seeds=np.array([o[2] for o in out]),
        out=np.stack([o[3] for o in out]),
        outputs=output_neurons(conn),
        captions=np.array(captions(args.posts)),
        trials=np.array(args.trials),
    )
    print(f"{len(jobs)} deneme, {time.perf_counter() - t0:.0f} sn → {path}")
    summarize(path)


if __name__ == "__main__":
    main()
