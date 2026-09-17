"""Oturum kaydından paylaşılabilir video (Faz 6).

Kare düzeni (1280 × 720):
  üst sol   sinek ve telefon ekranı (MuJoCo, kayıttaki duruşlardan; kamera sineğin arkasında)
  üst sağ   sinir sistemi: bütün nöronların y ekseni boyunca izdüşümü, son spike'lar parlak
  alt       sineğin gözleri, telefon ekranı, son karar ve gerekçesi

Oynatma hızı 1'den küçükse video "ağır çekim" diye etiketlenir (Z-28). Görüntünün tamamı
kayıttan gelir; simülasyon yeniden çalıştırılmaz.

Kullanım:
    python -m flybrain.viz.video runs/oturum-<ad> [--hiz 0.5] [--bas 0] [--son 20] [--cikti video.mp4]
"""

import argparse
import math
from pathlib import Path

import imageio.v2 as imageio
import mujoco as mj
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from flybrain.viz.record import load, spikes_between
from flybrain.viz.replay import Replay

W, H = 1280, 720
TOP = 480
TAU_MS = 60.0
BASE = 0.32
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
ACTION = {
    "ileri": "sonraki post", "geri": "önceki post", "begen": "beğen", "kaydet": "kaydet",
    "yorum": "yorum", "takip": "takip et", "cikis": "çıkış", "sekme_sol": "sekme (sol)",
    "sekme_sag": "sekme (sağ)", "timar": "tımar", "ilgi_kaybi": "ilgi kaybı",
}
GROUP_COLORS = [  # web/app.js SINIF_GRUBU ile aynı sıra ve renkler
    ("#3987e5", lambda c: c.startswith("ol_") or c.startswith("visual")),
    ("#199e70", lambda c: c == "cb_intrinsic"),
    ("#9085e9", lambda c: c == "vnc_intrinsic"),
    ("#c98500", lambda c: "sensory" in c),
    ("#d55181", lambda c: c.startswith(("descending", "ascending")) or "_ascending" in c or "_descending" in c),
    ("#e66767", lambda c: "motor" in c or "efferent" in c),
    ("#8a8a80", lambda c: True),
]


def _font(size: int):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default(size=size)


EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"


def _is_emoji(ch: str) -> bool:
    c = ord(ch)
    return c >= 0x1F000 or 0x2600 <= c <= 0x27BF


def _emoji(ch: str, size: int) -> Image.Image | None:
    try:
        font = ImageFont.truetype(EMOJI_FONT, 160)  # renkli emoji yazı tipi yalnızca bu boyutta
    except OSError:
        return None
    im = Image.new("RGBA", (200, 200))
    ImageDraw.Draw(im).text((0, 0), ch, font=font, embedded_color=True)
    box = im.getbbox()
    return im.crop(box).resize((size, size), Image.LANCZOS) if box else None


def draw_text(canvas: Image.Image, xy: tuple[int, int], text: str, fill, font) -> None:
    """Metni çizer; emojileri renkli emoji yazı tipiyle araya yerleştirir (caption'larda var)."""
    d = ImageDraw.Draw(canvas)
    x, y = xy
    size = int(font.size * 1.05)
    run = ""
    for ch in text + "\0":
        if ch in "\ufe0f\u200d":  # görünmez emoji birleştiricileri
            continue
        if ch != "\0" and not _is_emoji(ch):
            run += ch
            continue
        if run:
            d.text((x, y), run, fill=fill, font=font)
            x += int(d.textlength(run, font=font))
            run = ""
        if ch != "\0":
            icon = _emoji(ch, size)
            if icon is not None:
                canvas.paste(icon, (x, y + 1), icon)
                x += size + 2


def _hex(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


class BrainImage:
    """Nöronların y ekseni boyunca izdüşümü; spike'lar üstel sönümle parlar (web panelindeki gibi)."""

    def __init__(self, rec: dict, width: int, height: int):
        web = rec["yol"] / "web"
        pos = np.fromfile(web / "noron_konum.bin", np.float32).reshape(-1, 3)
        cls = np.fromfile(web / "noron_sinif.bin", np.uint8)
        import json

        classes = json.loads((web / "noronlar.json").read_text())["siniflar"]
        group = [next(i for i, (_, f) in enumerate(GROUP_COLORS) if f(c)) for c in classes]
        colors = np.stack([_hex(h) for h, _ in GROUP_COLORS])[np.array(group)[cls]]
        sx, sy = -pos[:, 0], pos[:, 2]  # beyin üstte, sinir kordonu altta
        pad = 16
        scale = min((width - 2 * pad) / np.ptp(sx), (height - 2 * pad) / np.ptp(sy))
        self.px = np.clip(((sx - sx.min()) * scale + (width - np.ptp(sx) * scale) / 2).astype(int), 0, width - 1)
        self.py = np.clip(((sy - sy.min()) * scale + (height - np.ptp(sy) * scale) / 2).astype(int), 0, height - 1)
        self.w, self.h = width, height
        base = np.zeros((height, width, 3))
        np.maximum.at(base, (self.py, self.px), colors * BASE)
        self.base = base
        self.level = np.zeros(len(pos))
        self.rec = rec
        self.shown = None

    def at(self, t_ms: float) -> np.ndarray:
        now = int(t_ms)
        if self.shown is None or now < self.shown or now - self.shown > 300:
            self.level[:] = 0
            for ms in range(max(0, now - int(5 * TAU_MS)), now):
                idx = spikes_between(self.rec, ms, ms + 1)
                np.add.at(self.level, idx, math.exp(-(now - ms) / TAU_MS))
        elif now > self.shown:
            self.level *= math.exp(-(now - self.shown) / TAU_MS)
            np.add.at(self.level, spikes_between(self.rec, self.shown, now), 1.0)
        self.shown = now
        img = self.base.copy()
        hot = np.flatnonzero(self.level > 0.03)
        v = np.minimum(1.0, self.level[hot])[:, None] * np.array([1.0, 0.8, 0.45])
        np.add.at(img, (self.py[hot], self.px[hot]), v)
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)


class VideoFrames:
    """Kayıttaki videodan zamana göre kare (ileri doğru okur, gerekirse baştan açar)."""

    def __init__(self, path: Path, frame_ms: float):
        self.path, self.frame_ms = path, frame_ms
        self.reader = imageio.get_reader(path)
        self.index, self.frame = -1, None

    def at(self, t_ms: float) -> np.ndarray:
        i = max(0, int(t_ms // self.frame_ms) - 1)
        if i < self.index:
            self.reader.close()
            self.reader = imageio.get_reader(self.path)
            self.index, self.frame = -1, None
        while self.index < i:
            try:
                self.frame = self.reader.get_next_data()
            except (IndexError, StopIteration):
                break
            self.index += 1
        return self.frame

    def close(self):
        self.reader.close()


def _fit(img: np.ndarray, w: int, h: int) -> Image.Image:
    im = Image.fromarray(img)
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)


def export_video(path: str | Path, out: str | Path | None = None, speed: float = 1.0, fps: float = 30.0,
                 start_ms: float = 0.0, end_ms: float | None = None) -> Path:
    path = Path(path)
    if not (path / "web" / "noron_konum.bin").exists():
        from flybrain.viz.export import export

        export(path)
    rec = load(path)
    meta, events = rec["meta"], rec["olaylar"]
    end_ms = min(end_ms or meta["sure_ms"], meta["sure_ms"])
    out = Path(out) if out else path / ("video.mp4" if speed == 1 else f"video-{speed:g}x.mp4")

    rp = Replay(rec, 640, TOP)
    scene = rp.body.scene
    scene.register(rp.renderer)
    screen_shape = scene._pixels.shape
    thorax, screen_body = rp._thorax, mj.mj_name2id(rp.m, mj.mjtObj.mjOBJ_BODY, "ekran")
    rp.pose(start_ms)
    ahead = rp.d.xpos[screen_body][:2] - rp.d.xpos[thorax][:2]
    rp.camera.azimuth = math.degrees(math.atan2(ahead[1], ahead[0])) + 35.0
    rp.camera.elevation, rp.camera.distance = -22.0, 5.2

    brain = BrainImage(rec, 640, TOP)
    eyes = VideoFrames(path / "gozler.mp4", meta["kare_araligi_ms"])
    phone = VideoFrames(path / "ekran.mp4", meta["kare_araligi_ms"])
    big, mid, small = _font(22), _font(16), _font(13)
    decisions = [e for e in events if e["tur"] == "karar"]
    posts = [e for e in events if e["tur"] == "post"]
    label = "gerçek hız" if speed == 1 else (f"ağır çekim {speed:g}×" if speed < 1 else f"{speed:g}× hızlı")

    writer = imageio.get_writer(out, fps=fps, macro_block_size=1, quality=8, ffmpeg_log_level="error")
    try:
        n = int((end_ms - start_ms) / (1000 / fps * speed))
        for k in range(n):
            t = start_ms + k * 1000 / fps * speed
            shot = phone.at(t)
            if shot is not None:
                scene.show(np.asarray(Image.fromarray(shot).resize(screen_shape[1::-1], Image.BILINEAR)))
            fly = rp.render(t, hide_screen=False)
            canvas = Image.new("RGB", (W, H), (17, 18, 20))
            canvas.paste(Image.fromarray(fly), (0, 0))
            canvas.paste(Image.fromarray(brain.at(t)), (640, 0))
            x = 8
            eye = eyes.at(t)
            if eye is not None:
                im = _fit(eye, 420, H - TOP - 16)
                canvas.paste(im, (x, TOP + 8))
                x += im.width + 8
            if shot is not None:
                im = _fit(shot, 200, H - TOP - 16)
                canvas.paste(im, (x, TOP + 8))
                x += im.width + 16
            d = ImageDraw.Draw(canvas)
            d.text((12, 10), f"t = {t / 1000:5.2f} sn · {label}", fill=(236, 235, 230), font=mid)
            if rp.held[rp.index(t)]:
                d.text((12, 32), "deneyci sineği tutuyor", fill=(240, 180, 41), font=mid)
            d.text((652, 10), f"sinir sistemi · {meta['noron_sayisi']:,} nöron".replace(",", "."), fill=(236, 235, 230), font=mid)
            d.text((652, 30), "parlak: son ~60 ms'de spike atanlar", fill=(154, 153, 143), font=small)
            post = next((p for p in reversed(posts) if p["t_ms"] <= t), None)
            dec = next((e for e in reversed(decisions) if e["t_ms"] <= t), None)
            y = TOP + 12
            if post:
                draw_text(canvas, (x, y), f"post {post['sira']}: “{post['aciklama']}”", (154, 153, 143), small)
                y += 24
            if post and (dec is None or dec["sira"] != post["sira"]):
                d.text((x, y), f"bakıyor… {(t - post['t_ms']) / 1000:.1f} sn", fill=(236, 235, 230), font=big)
            elif dec:
                d.text((x, y), ACTION.get(dec["eylem"], dec["eylem"]), fill=(240, 180, 41), font=big)
                d.text((x, y + 32), dec["gerekce"], fill=(154, 153, 143), font=small)
            y = TOP + 110
            for e in [e for e in decisions if e["t_ms"] <= t][-5:]:
                d.text((x, y), f"{e['t_ms'] / 1000:5.1f} sn  #{e['sira']:<3} {ACTION.get(e['eylem'], e['eylem'])}",
                       fill=(154, 153, 143), font=small)
                y += 18
            writer.append_data(np.asarray(canvas))
    finally:
        writer.close()
        eyes.close()
        phone.close()
        rp.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kayit")
    ap.add_argument("--hiz", type=float, default=1.0, help="oynatma hızı (0,5 = ağır çekim)")
    ap.add_argument("--bas", type=float, default=0.0, help="başlangıç (sn)")
    ap.add_argument("--son", type=float, help="bitiş (sn)")
    ap.add_argument("--cikti")
    args = ap.parse_args()
    out = export_video(args.kayit, args.cikti, args.hiz, start_ms=args.bas * 1000,
                       end_ms=None if args.son is None else args.son * 1000)
    print(f"video: {out}")


if __name__ == "__main__":
    main()
