"""Yaklaşan nesne → kaçış (Z-25) ve durağan ekranda kendiliğinden kaçış.

Yaklaşma uyaranı telefon ekranında, bakılan postun görselinde oynayan bir videodur: post
görselinin üstünde büyüyen koyu bir disk. Diskin açısal boyutu, sabit hızla yaklaşan bir
nesnenin boyutudur (dev lif deneylerindeki uyaran türü; von Reyn ve ark. 2014):

    ψ(t) = atan(l/v / τ(t))      ψ: yarı açı, τ: çarpışmaya kalan süre, l/v: boy / hız

l/v = 40 ms bir VARSAYIM (literatürde 10-80 ms aralığında farklı değerler kullanılıyor).

Disk 10°'lik tam açıdan 160°'ye büyür, sonra sabit kalır. Kavisli ekranda her pikselin
sineğin gözünden bakış yönü hesaplanır (scene.pixel_directions); disk, merkez yönüne açısal
uzaklığı ψ'den küçük olan piksellerdir.

Her deneme: ekran açık (post), sinek oturur, BASE_MS bakar; sonra ya yaklaşma videosu
oynar ("yaklasma") ya da hiçbir şey değişmez ("duragan"). Dışarıdan uyarım yok.
Görme kazancı (VisionConfig.r_max_hz) taranır: durağan ekranda kendiliğinden kaçış ile
yaklaşmaya kaçış arasındaki dengeyi görmek için. Seçilen değer 125 Hz (K-029).

Uzun durağan deneme (--uzun-duragan MS): yalnızca durağan ekran, verilen süre boyunca;
kendiliğinden kaçışın sıklığı için.

Kullanım:
    python -m flybrain.experiments.escape --video   # tek yaklaşma denemesinin videosu (ağır çekim)
    python -m flybrain.experiments.escape [--rmax 250 150 125 100 75] [--trials 8] [--workers 4]
    python -m flybrain.experiments.escape --uzun-duragan 3000 --rmax 150 125 100 --trials 6
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.paths import RUNS

L_OVER_V_MS = 40.0
START_DEG = 10.0      # tam açı
STOP_DEG = 160.0
HOLD_MS = 300.0
CENTER_ELEVATION_DEG = 10.0
BASE_MS = 300.0
JUMP_MM = 1.0         # göğüs bu kadar yer değiştirirse sıçrama sayılır


def looming_video(background: np.ndarray, dirs: np.ndarray, l_over_v_ms: float = L_OVER_V_MS,
                  elevation_deg: float = CENTER_ELEVATION_DEG):
    """background: post görseli (uint8); dirs: görselin piksellerinin bakış yönleri.

    Dönüş: (video(t_ms), çarpışma anı [ms, video başından]).
    """
    el = np.radians(elevation_deg)
    center = np.array([np.cos(el), 0.0, np.sin(el)])
    cos_dist = dirs @ center
    tau0 = l_over_v_ms / np.tan(np.radians(START_DEG) / 2)
    t_stop = tau0 - l_over_v_ms / np.tan(np.radians(STOP_DEG) / 2)

    def video(t_ms: float) -> np.ndarray | None:
        if t_ms > t_stop + HOLD_MS:
            return None
        psi = np.arctan(l_over_v_ms / (tau0 - min(t_ms, t_stop)))
        frame = background.copy()
        frame[cos_dist >= np.cos(psi)] = 0
        return frame

    return video, tau0


def _trials(r_max: float, kinds: list[str], n: int, seed: int, static_ms: float | None = None) -> list[dict]:
    from flybrain.body.embodied import EmbodiedFly
    from flybrain.body.phone import PhoneFeed, fit, post_box
    from flybrain.body.scene import SceneConfig, pixel_directions
    from flybrain.experiments.scene import _Counter, _groups, _post
    from flybrain.senses.vision import VisionConfig

    cfg = SceneConfig()
    fly = EmbodiedFly(vision=VisionConfig(mode="onoff", r_max_hz=r_max), scene=cfg, seed=seed)
    counter = _Counter(fly, _groups(fly))
    top, bottom, left, right = post_box(cfg.texture_shape)
    rows, cols = np.mgrid[top:bottom, left:right]
    dirs = pixel_directions(cfg, rows, cols)
    out = []
    for k in range(n):
        for kind in kinds:
            post = _post(k)
            fly.feed = PhoneFeed(cfg.texture_shape, previous=_post(100 + k))
            fly.show_post(post)
            fly.reset()
            counter.log.clear()
            t0 = fly.brain.time_ms
            trace = fly.run(BASE_MS)
            t_event = fly.brain.time_ms
            video, t_coll = looming_video(fit(post.image, right - left, bottom - top), dirs)
            if kind == "yaklasma":
                fly.play_video(video)
            duration = t_coll + HOLD_MS if static_ms is None else static_ms
            fly.run(duration, trace=trace)
            a = trace.arrays()
            t = a["t_ms"]
            L = np.array(counter.log)
            gf_t = L[L[:, 1] > 0, 0]
            base = t <= t_event
            after = t > t_event
            disp = np.linalg.norm(a["thorax"][:, :2] - a["thorax"][0, :2], axis=1)
            dz = a["thorax"][:, 2] - a["thorax"][base, 2].mean()
            jumped = (disp[after] > JUMP_MM) | (dz[after] > JUMP_MM)
            first_gf = gf_t[gf_t > t_event]
            out.append({
                "rmax": r_max, "tur": kind, "post": k, "seed": seed, "sure_ms": duration,
                "gf_once": int(L[(L[:, 0] > t0) & (L[:, 0] <= t_event), 1].sum()),
                "gf_sonra": int(L[L[:, 0] > t_event, 1].sum()),
                "lc4_sonra": int(L[L[:, 0] > t_event, 2].sum()),
                "ilk_gf_carpismaya_gore_ms": float(first_gf[0] - t_event - t_coll) if len(first_gf) else None,
                "sicrama": bool(jumped.any()),
                "sicrama_carpismaya_gore_ms": float(t[after][jumped][0] - t_event - t_coll) if jumped.any() else None,
                "gorme_once_khz": round(float(a["vision_hz"][base].mean()) / 1000, 1),
            })
    return out


def demo_video(seed: int = 1, slowdown: int = 4) -> str:
    """Yaklaşma denemesi: dışarıdan görünüm ve sineğin gözleri, ağır çekim."""
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.phone import fit, post_box
    from flybrain.body.scene import SceneConfig, pixel_directions
    from flybrain.experiments.scene import _post, recorder, write_video

    cfg = SceneConfig()
    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=cfg, seed=seed)
    top, bottom, left, right = post_box(cfg.texture_shape)
    rows, cols = np.mgrid[top:bottom, left:right]
    post = _post(0)
    fly.show_post(post)
    fly.reset()
    frames = []
    grab = recorder(frames)
    fly.run(BASE_MS, on_step=grab)
    video, t_coll = looming_video(fit(post.image, right - left, bottom - top), pixel_directions(cfg, rows, cols))
    fly.play_video(video)
    fly.run(t_coll + HOLD_MS + 400, on_step=grab)
    return str(write_video(frames, f"escape-yaklasma-{seed}", slowdown=slowdown))


def summarize(rows: list[dict]) -> dict:
    out = {}
    for r_max in sorted({r["rmax"] for r in rows}, reverse=True):
        for kind in ("duragan", "yaklasma"):
            sel = [r for r in rows if r["rmax"] == r_max and r["tur"] == kind]
            if not sel:
                continue
            clean = [r for r in sel if r["gf_once"] == 0]
            lat = [r["ilk_gf_carpismaya_gore_ms"] for r in clean if r["ilk_gf_carpismaya_gore_ms"] is not None]
            out[f"{r_max:g}/{kind}"] = {
                "deneme": len(sel),
                "beklemede_kacis": sum(r["gf_once"] > 0 for r in sel),
                "temiz": len(clean),
                "dev_lif_ateslenen": sum(r["gf_sonra"] > 0 for r in clean),
                "sicrayan": sum(r["sicrama"] for r in clean),
                "ilk_gf_ms_medyan": float(np.median(lat)) if lat else None,
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rmax", type=float, nargs="+", default=[250.0, 150.0, 125.0, 100.0, 75.0])
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--uzun-duragan", type=float, default=None, metavar="MS")
    ap.add_argument("--video", action="store_true")
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    if args.video:
        print(demo_video(seed=1))
        return
    t_start = time.perf_counter()
    kinds = ["duragan"] if args.uzun_duragan else ["duragan", "yaklasma"]
    with ProcessPoolExecutor(args.workers) as ex:
        futures = [ex.submit(_trials, r, kinds, args.trials, args.seed, args.uzun_duragan) for r in args.rmax]
        rows = [row for f in futures for row in f.result()]
    out = {"ayarlar": {"l_over_v_ms": L_OVER_V_MS, "baslangic_deg": START_DEG, "bitis_deg": STOP_DEG,
                       "yukseklik_deg": CENTER_ELEVATION_DEG, "bekleme_ms": BASE_MS,
                       "uzun_duragan_ms": args.uzun_duragan},
           "ozet": summarize(rows), "denemeler": rows, "sure_sn": round(time.perf_counter() - t_start, 1)}
    tag = "-uzun" if args.uzun_duragan else ""
    path = RUNS / f"escape{tag}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out["ozet"], indent=1, ensure_ascii=False))
    print(f"süre {out['sure_sn']} sn; sonuçlar: {path}")


if __name__ == "__main__":
    main()
