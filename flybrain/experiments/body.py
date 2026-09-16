"""Gövde neden-sonuç deneyleri: uyarılan devre, beklenen gövde bölgesini hareket ettiriyor mu?

Yoklamalar (her biri: oturma, 300 ms sessiz başlangıç, uyarım, sessiz bitiş):
  sessiz   : hiç uyarım yok; motor nöronlar sessiz, gövde yalnızca pasif duruşa oturur
  mn9      : hortum motor nöronu MN9 doğrudan uyarılır → hortum ileri/açılma beklenir
  seker    : şeker tat nöronları (LB3b/c) → beyin → MN9 → hortum (uçtan uca)
  dev_lif  : dev lif (DNp01) kısa darbe → TTMn → orta bacaklar açılır → sıçrama
  ttmn     : sıçrama kası motor nöronu doğrudan (fizik ve kas modeli kontrolü)
  dev_lif_uzun : dev lif 150 ms boyunca (fizyolojik değil; iletimin eşiğini görmek için)
  dng100   : yürüme komut nöronu; inen nöronlar depresyondan muaf (Z-22) → bacaklar

Her yoklama bir video (runs/body-<ad>.mp4) ve ölçüm tablosu üretir. Propriyosepsiyon
varsayılan olarak açıktır; --no-proprio ile kapatılır (çıktılar runs/body-<ad>-p0.*).

Kullanım:
    python -m flybrain.experiments.body [--probes mn9 dev_lif] [--workers 5] [--no-video] [--no-proprio]
    python -m flybrain.experiments.body --montage   # üç deneyi yan yana, etiketli tek video
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.paths import RUNS

PROBES = {
    "sessiz": {"pre": 300, "stim": 1000, "post": 0, "hz": 0.0, "types": []},
    "mn9": {"pre": 300, "stim": 600, "post": 400, "hz": 150.0, "types": ["MN9"]},
    "seker": {"pre": 300, "stim": 800, "post": 400, "hz": 150.0, "types": ["LB3b", "LB3c"]},
    "dev_lif": {"pre": 300, "stim": 15, "post": 400, "hz": 300.0, "types": ["DNp01"]},
    "ttmn": {"pre": 300, "stim": 10, "post": 400, "hz": 300.0, "types": ["TTMn"]},
    "dev_lif_uzun": {"pre": 300, "stim": 150, "post": 400, "hz": 300.0, "types": ["DNp01"]},
    "dng100": {"pre": 300, "stim": 1500, "post": 300, "hz": 150.0, "types": ["DNg100"], "exempt": "descending"},
}

WATCH = {
    "rostrum": "c_head-c_rostrum-pitch",
    "haustellum": "c_rostrum-c_haustellum-pitch",
    "bas": "c_thorax-c_head-roll",
    "sol_kanat": "c_thorax-l_wing-roll",
    "karin": "c_abdomen3-c_abdomen4-pitch",
    "lm_trokanter": "lm_coxa-lm_trochanterfemur-pitch",
    "rm_trokanter": "rm_coxa-rm_trochanterfemur-pitch",
    "lf_tibia": "lf_trochanterfemur-lf_tibia-pitch",
}


def _up_vectors(quats: np.ndarray) -> np.ndarray:
    """Gövdenin sırt yönü (yerel +z) dünya çerçevesinde; quat = (w, x, y, z)."""
    w, x, y, z = quats.T
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], axis=1)


def run_probe(name: str, video: bool = True, seed: int = 0, proprio: bool = True) -> dict:
    from flybrain.body.embodied import EmbodiedFly
    from flybrain.connectome.connectome import load_connectome
    from flybrain.sim import Stimulus

    p = PROBES[name]
    conn = load_connectome()
    t = conn.neurons["type"].fillna("").astype(str).to_numpy(dtype=object)
    exempt = None
    if p.get("exempt") == "descending":
        exempt = np.flatnonzero(conn.neurons.superclass.fillna("").astype(str).to_numpy(dtype=object) == "descending_neuron")
    fly = EmbodiedFly(conn, seed=seed, std_exempt=exempt, proprioception=proprio)
    tag = name if proprio else f"{name}-p0"
    stim_idx = np.flatnonzero(np.isin(t, p["types"]))
    stim = Stimulus.of(stim_idx, p["hz"]) if len(stim_idx) else None
    cams = ("yan", "izleme") if video else ()

    fly.reset()
    t0 = time.time()
    trace = fly.run(p["pre"], None, cameras=cams)
    n_pre = len(trace.t_ms)
    fly.run(p["stim"], stim, cameras=cams, trace=trace)
    n_stim = len(trace.t_ms)
    if p["post"]:
        fly.run(p["post"], None, cameras=cams, trace=trace)
    wall = time.time() - t0
    a = trace.arrays()
    sim_ms = p["pre"] + p["stim"] + p["post"]

    ang = a["angles"]
    base = ang[n_pre - 1]
    out = {"ad": tag, "sure_ms": sim_ms, "duvar_sn": round(wall, 1), "uyarilan": int(len(stim_idx))}
    for label, joint in WATCH.items():
        j = fly.joint(joint)
        dev = ang[n_pre:, j] - base[j]
        out[f"{label}_max_sapma_rad"] = round(float(dev[np.argmax(np.abs(dev))]), 3)
    th = a["thorax"]
    out["gogus_yukseklik_basta_mm"] = round(float(th[n_pre - 1, 2]), 3)
    out["gogus_yukseklik_max_mm"] = round(float(th[n_pre:, 2].max()), 3)
    out["gogus_yatay_yol_mm"] = round(float(np.linalg.norm(np.diff(th[n_pre:, :2], axis=0), axis=1).sum()), 3)
    up = _up_vectors(a["thorax_quat"])
    out["sirt_egimi_max_derece"] = round(float(np.degrees(np.arccos(np.clip(up[n_pre:, 2], -1, 1))).max()), 1)
    out["gogus_net_yer_degistirme_mm"] = round(float(np.linalg.norm(th[-1, :2] - th[n_pre - 1, :2])), 3)
    # Kas grubu başına motor nöron spike'ları (uyarım + sonrası).
    spikes = a["mn_spikes"][n_pre:].sum(axis=0)
    groups = {}
    pos = {int(n): i for i, n in enumerate(fly.muscles.mn)}
    for m in fly.table.muscles:
        g = m.name.split(":")[0]
        g = "bacak" if len(g) == 2 else g
        groups[g] = groups.get(g, 0) + int(spikes[[pos[int(i)] for i in m.mn]].sum())
    out["mn_spike"] = groups
    out["mn_spike_sessiz_baslangic"] = int(a["mn_spikes"][:n_pre].sum())
    if proprio:
        out["propriyo_spike"] = int(a["proprio_spikes"][n_pre:].sum())
    act = a["activation"]
    top = np.argsort(-act.max(axis=0))[:5]
    out["en_cok_uyarilan_kaslar"] = {fly.table.muscles[k].name: round(float(act[:, k].max()), 3) for k in top if act[:, k].max() > 0}

    if video:
        import imageio.v2 as imageio

        for cam, frames in trace.frames.items():
            path = RUNS / f"body-{tag}-{cam}.mp4"
            imageio.mimwrite(path, frames, fps=30, macro_block_size=1)
        out["video"] = [str(RUNS / f"body-{tag}-{c}.mp4") for c in trace.frames]
    np.savez_compressed(RUNS / f"body-{tag}.npz", **a, n_pre=n_pre, n_stim=n_stim,
                        joint_names=np.array(fly.body.joint_names), mn=fly.muscles.mn)
    fly.body.close()
    return out


MONTAGE = [
    ("mn9", "yan", "Hortum motor nöronu MN9 uyarılıyor", "beklenen: hortum uzar"),
    ("dev_lif", "yan", "Dev lif (kaçış nöronu) 15 ms uyarılıyor", "zincir: dev lif → TTMn → orta bacaklar"),
    ("dng100", "izleme", "Yürüme komut nöronu DNg100 uyarılıyor", "bacak motor nöronları çalışıyor; henüz koordinasyon yok"),
]
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"


def montage(path=None, slowdown: int = 4, fps: int = 30):
    """Kayıtlı deney videolarını yan yana koyar; uyarımın açık olduğu anları işaretler."""
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw, ImageFont

    path = path or RUNS / "govde-ilk-deneyler.mp4"
    font = ImageFont.truetype(FONT, 16)
    clips = [(imageio.mimread(RUNS / f"body-{n}-{c}.mp4", memtest=False), PROBES[n], title, sub)
             for n, c, title, sub in MONTAGE]
    h, w = clips[0][0][0].shape[:2]
    n = max(len(c[0]) for c in clips)
    out = []
    for k in range(n):
        t_ms = k * 1000 / fps
        canvas = Image.new("RGB", (w * len(clips), h + 70), (18, 18, 22))
        d = ImageDraw.Draw(canvas)
        for i, (frames, p, title, sub) in enumerate(clips):
            canvas.paste(Image.fromarray(frames[min(k, len(frames) - 1)]), (w * i, 70))
            on = p["pre"] <= t_ms < p["pre"] + p["stim"]
            d.text((w * i + 10, 8), title, font=font, fill=(240, 240, 240))
            d.text((w * i + 10, 30), sub, font=font, fill=(170, 170, 180))
            d.rounded_rectangle((w * i + 10, 78, w * i + 150, 104), 6, fill=(255, 90, 60) if on else (90, 90, 100))
            d.text((w * i + 18, 81), "UYARIM AÇIK" if on else "uyarım yok", font=font, fill=(255, 255, 255))
            t_clip = min(t_ms, (len(frames) - 1) * 1000 / fps)
            d.text((w * i + w - 90, 81), f"{t_clip:5.0f} ms", font=font, fill=(255, 255, 0))
        out.extend([np.asarray(canvas)] * slowdown)
    imageio.mimwrite(path, out, fps=fps, macro_block_size=1)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", nargs="+", default=list(PROBES))
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--montage", action="store_true")
    ap.add_argument("--no-proprio", action="store_true")
    args = ap.parse_args()
    if args.montage:
        print(montage())
        return
    RUNS.mkdir(exist_ok=True)
    with ProcessPoolExecutor(args.workers) as ex:
        n = len(args.probes)
        results = list(ex.map(run_probe, args.probes, [not args.no_video] * n, [0] * n, [not args.no_proprio] * n))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = RUNS / f"body-{stamp}.json"
    path.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
