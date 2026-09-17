"""Telefon ekranlı sahne (K-028): kapsama ve post geçişlerine beynin yanıtı.

Ölçümler:
  kapsama : göz kolonlarının kaçı ekranı, kaçı post görselini görüyor.
  gecis   : ekran baştan açık (post i), sinek oturur, 500 ms bakar; sonra post j'ye
            TRANSITIONS'taki yollardan biriyle geçilir; AFTER_MS izlenir.
            Sessiz beyin, dışarıdan uyarım yok. Dev lif (DNp01), LC4, inen nöronlar,
            bacak motor nöronları ve göğsün yer değiştirmesi kaydedilir.
  acilis  : ekran kapalıyken (siyah) 300 ms, sonra post açılır.

Geçişler ekran temalarıyla (phone.THEMES) ayrı ayrı ölçülebilir (--themes).

Her denemede sinek sıfırlanır (beyin ve gövde); ekranın akışı yeniden kurulur.

Kullanım:
    python -m flybrain.experiments.scene [--pairs 8] [--seeds 0] [--workers 4] [--video]
    python -m flybrain.experiments.scene --no-extras --modes kaydir --themes acik koyu gri
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.body.phone import DEFAULT_THEME, FADE_MS, THEMES
from flybrain.paths import RUNS

BASE_MS = 500.0
AFTER_MS = 1500.0
# Geçiş türleri: (yöntem, süre ms)
TRANSITIONS = {
    "ani": ("show", 0.0),
    "kaydir": ("scroll", 400.0),
    "kaydir_hizli": ("scroll", 250.0),
    "kaydir_yavas": ("scroll", 1200.0),
    "solma": ("fade", FADE_MS),
}
EARLY_MS = 100.0
IMAGE_SEED = 11


def _post(k: int):
    from flybrain.body.phone import FeedPost
    from flybrain.experiments.vision import natural_image

    return FeedPost(natural_image(k, IMAGE_SEED), username=f"hesap_{k}", caption=f"post {k}", likes=10 * k)


class _Counter:
    """LIF'in her adımında seçili nöron gruplarının spike'larını zamanla birlikte biriktirir."""

    def __init__(self, fly, groups: dict[str, np.ndarray]):
        self.groups = groups
        self.log: list[tuple[float, ...]] = []
        orig = fly.brain.run

        def run(d, s=None, **kw):
            r = orig(d, s, **kw)
            self.log.append((fly.brain.time_ms, *(int(r.counts[g].sum()) for g in groups.values())))
            return r

        fly.brain.run = run

    def window(self, lo: float, hi: float) -> dict[str, int]:
        L = np.array(self.log)
        m = (L[:, 0] > lo) & (L[:, 0] <= hi)
        return {name: int(L[m, k + 1].sum()) for k, name in enumerate(self.groups)}


def _fly(seed: int):
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.scene import SceneConfig

    return EmbodiedFly(vision=EMBODIED_VISION, scene=SceneConfig(), seed=seed)


def _groups(fly) -> dict[str, np.ndarray]:
    t = fly.conn.neurons.type.fillna("").to_numpy(dtype=object)
    return {
        "dev_lif": np.flatnonzero(t == "DNp01"),
        "lc4": np.flatnonzero(t == "LC4"),
        "inen": fly.conn.select(superclass="descending_neuron"),
    }


def _summary(fly, counter, trace, t0: float, t_event: float) -> dict:
    a = trace.arrays()
    t = a["t_ms"]
    disp = np.linalg.norm(a["thorax"][:, :2] - a["thorax"][0, :2], axis=1)

    def part(lo, hi):
        m = (t > lo) & (t <= hi)
        out = counter.window(lo, hi)
        out["mn"] = int(a["mn_spikes"][m].sum())
        out["gorme_khz"] = round(float(a["vision_hz"][m].mean()) / 1000, 1) if m.any() else 0.0
        return out

    return {
        "once": part(t0, t_event),
        "ilk_100ms": part(t_event, t_event + EARLY_MS),
        "sonra": part(t_event + EARLY_MS, t[-1]),
        "gogus_mm": round(float(disp.max()), 3),
    }


def transitions(pairs: list[tuple[int, int]], seed: int, mode: str, theme: str = DEFAULT_THEME) -> list[dict]:
    from flybrain.body.phone import PhoneFeed

    fly = _fly(seed)
    counter = _Counter(fly, _groups(fly))
    out = []
    for i, j in pairs:
        fly.feed = PhoneFeed(fly.scene.cfg.texture_shape, previous=_post(100 + i), theme=theme)
        fly.show_post(_post(i))
        fly.reset()
        counter.log.clear()
        t0 = fly.brain.time_ms
        trace = fly.run(BASE_MS)
        t_event = fly.brain.time_ms
        kind, duration = TRANSITIONS[mode]
        if kind == "show":
            fly.show_post(_post(j))
        elif kind == "scroll":
            fly.scroll_to_post(_post(j), duration)
        else:
            fly.fade_to_post(_post(j), duration)
        fly.run(AFTER_MS, trace=trace)
        out.append({"i": i, "j": j, "yontem": mode, "tema": theme, "seed": seed,
                    **_summary(fly, counter, trace, t0, t_event)})
    return out


def onset(seed: int, video: bool = False) -> dict:
    """Ekran kapalıyken başlar, 300 ms sonra açılır."""
    fly = _fly(seed)
    counter = _Counter(fly, _groups(fly))
    fly.reset()
    frames = []
    grab = recorder(frames) if video else None
    t0 = fly.brain.time_ms
    trace = fly.run(300, on_step=grab)
    t_event = fly.brain.time_ms
    fly.show_post(_post(0))
    fly.run(1200, on_step=grab, trace=trace)
    out = {"deney": "acilis", "seed": seed, **_summary(fly, counter, trace, t0, t_event)}
    if video:
        out["video"] = str(write_video(frames, f"scene-acilis-{seed}"))
    return out


def transition_video(seed: int = 0, theme: str = DEFAULT_THEME, mode: str = "solma") -> str:
    """Ekran açık, sinek bakar, akış iki kez sonraki posta geçer (TRANSITIONS[mode])."""
    from flybrain.body.phone import PhoneFeed

    def go(post):
        kind, duration = TRANSITIONS[mode]
        if kind == "show":
            fly.show_post(post)
        elif kind == "scroll":
            fly.scroll_to_post(post, duration)
        else:
            fly.fade_to_post(post, duration)

    fly = _fly(seed)
    fly.feed = PhoneFeed(fly.scene.cfg.texture_shape, previous=_post(100), theme=theme)
    fly.show_post(_post(0))
    fly.reset()
    frames = []
    grab = recorder(frames)
    trace = fly.run(600, on_step=grab)
    go(_post(1))
    fly.run(1500, on_step=grab, trace=trace)
    go(_post(4))
    fly.run(1500, on_step=grab, trace=trace)
    return str(write_video(frames, f"scene-{mode}-{theme}-{seed}"))


def recorder(frames: list, fps: float = 30.0, camera: str = "izleme"):
    """EmbodiedFly.run için on_step: üstte dışarıdan görünüm, altta sineğin iki gözü (sol | sağ)."""
    from PIL import Image

    every = int(round(1000 / fps))

    def grab(fly):
        if int(round(fly.brain.time_ms)) % every:
            return
        outside = fly.body.render(camera)
        w = outside.shape[1]
        eyes = fly.eyes.last_frames
        if eyes:
            view = np.concatenate([eyes["L"], eyes["R"]], axis=1)  # uint8
            h = 2 * int(round(w * view.shape[0] / view.shape[1] / 2))  # video kodlayıcı çift boyut ister
            view = np.asarray(Image.fromarray(view).resize((w, h)))
        else:
            view = np.zeros((w // 2, w, 3), np.uint8)
        frames.append(np.concatenate([outside, view], axis=0))

    return grab


def write_video(frames: list, name: str, fps: float = 30.0, slowdown: int = 1):
    """Kareler simülasyon zamanında 30 kare/sn; slowdown > 1 ağır çekim."""
    import imageio.v2 as imageio

    path = RUNS / f"{name}.mp4"
    imageio.mimwrite(path, frames, fps=fps / slowdown, macro_block_size=1)
    return path


def coverage() -> dict:
    from flybrain.body.phone import post_box

    fly = _fly(0)
    fly.reset()
    shape = fly.scene.cfg.texture_shape
    top, bottom, left, right = post_box(shape)
    only_post = np.zeros(shape + (3,), np.uint8)
    only_post[top:bottom, left:right] = 255
    counts = {}
    for name, img in (("post", only_post), ("ekran", np.full(shape + (3,), 255, np.uint8))):
        fly.scene.show(img)
        values = fly.eyes.column_values()
        counts[name] = sum(int(np.nansum(values[g[0]]["lum"] > 0.75)) for g in fly.eyes.groups)
    total = sum(len(g[1]) for g in fly.eyes.groups)
    return {"kolon": total, **{k: {"sayi": v, "oran": round(v / total, 3)} for k, v in counts.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=8)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--modes", nargs="+", default=list(TRANSITIONS), choices=list(TRANSITIONS))
    ap.add_argument("--themes", nargs="+", default=[DEFAULT_THEME], choices=list(THEMES))
    ap.add_argument("--no-extras", action="store_true", help="kapsama ve açılış ölçümlerini atla")
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    t_start = time.perf_counter()
    rng = np.random.default_rng(0)
    pairs = [tuple(int(x) for x in rng.choice(12, 2, replace=False)) for _ in range(args.pairs)]
    chunks = [pairs[k::args.workers] for k in range(args.workers)]
    jobs = [(c, s, m, th) for th in args.themes for s in args.seeds for m in args.modes for c in chunks if c]
    with ProcessPoolExecutor(args.workers) as ex:
        results = {}
        if not args.no_extras:
            results["kapsama"] = ex.submit(coverage)
            results["acilis"] = [ex.submit(onset, s, args.video) for s in args.seeds]
        if args.video:
            results["gecis_video"] = [ex.submit(transition_video, args.seeds[0], th, args.modes[0])
                                      for th in args.themes]
        runs = [ex.submit(transitions, *j) for j in jobs]
        out = {k: (v.result() if not isinstance(v, list) else [x.result() for x in v]) for k, v in results.items()}
        out["gecis"] = [r for f in runs for r in f.result()]
    rows = out["gecis"]
    out["ozet"] = {}
    for th, mode in [(th, m) for th in args.themes for m in args.modes]:
        sel = [r for r in rows if r["yontem"] == mode and r["tema"] == th]
        out["ozet"][f"{th}/{mode}"] = {
            "deneme": len(sel),
            "dev_lif_ateslenen": sum(r["ilk_100ms"]["dev_lif"] + r["sonra"]["dev_lif"] > 0 for r in sel),
            "dev_lif_spike_ort": round(float(np.mean([r["ilk_100ms"]["dev_lif"] + r["sonra"]["dev_lif"] for r in sel])), 1),
            "gogus_mm_ort": round(float(np.mean([r["gogus_mm"] for r in sel])), 3),
            "gorme_ilk_100ms_khz": round(float(np.mean([r["ilk_100ms"]["gorme_khz"] for r in sel])), 1),
        }
    out["sure_sn"] = round(time.perf_counter() - t_start, 1)
    path = RUNS / f"scene-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("kapsama", "ozet", "sure_sn") if k in out}, indent=1, ensure_ascii=False))
    for r in out.get("acilis", []):
        print("açılış", r)
    for r in rows:
        print(r["tema"], r["yontem"], r["i"], "->", r["j"], "dev lif", r["ilk_100ms"]["dev_lif"], r["sonra"]["dev_lif"],
              "LC4", r["ilk_100ms"]["lc4"], r["sonra"]["lc4"], "göğüs", r["gogus_mm"])
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
