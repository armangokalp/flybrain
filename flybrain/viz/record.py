"""Oturum kaydı (Faz 6): kapalı döngünün sonradan izlenebilen, yeniden çizilebilen kaydı.

Kayıt bir dizindir (runs/oturum-<zaman>/). Bütün zamanlar kaydın başından itibaren ms:
  meta.json      kayıt bilgisi: sinek, süre, aralıklar, video boyutları
  olaylar.json   zaman sıralı olaylar: post başlangıcı, karar (gerekçesi ve gövde ölçüleriyle),
                 deneycinin yeniden yerleştirmesi
  govde.npz      t_ms, qpos (MuJoCo durum vektörü, float32), mocap (telefon ekranı gibi fizik dışı
                 gövdelerin konumu ve dörtlüsü, [kare, gövde, 7]), tutuluyor (deneyci sineği tutuyor mu)
  spikes.npz     ofset, noron: i. milisaniyede ateşleyen nöronlar noron[ofset[i]:ofset[i+1]];
                 indeksler konnektomun sırasında (connectome.load_connectome().neurons)
  gozler.mp4     sineğin iki gözünün kamera görüntüsü (sol | sağ)
  ekran.mp4      telefon ekranı
  kareler.npz    t_ms: video karelerinin zamanları (iki videoda aynı)

Gövde qpos'tan yeniden kurulur (mj_forward); sahne herhangi bir kameradan sonradan çizilebilir
(viz/replay.py). Kaydedici EmbodiedFly.recorder olarak bağlanır; sinek her 1 ms'lik adımın
sonunda, fizikten ve deneycinin müdahalesinden sonra `step` çağırır.
"""

import json
import time
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image

from flybrain.paths import RUNS

FPS = 30.0
BODY_EVERY_MS = 5
VIDEO_SCALE = 0.5


def _even(img: np.ndarray, scale: float) -> np.ndarray:
    """Ölçeklenmiş, kenarları çift sayı olan kare (video kodlayıcı çift boyut ister)."""
    h, w = img.shape[:2]
    size = (2 * max(1, int(round(w * scale / 2))), 2 * max(1, int(round(h * scale / 2))))
    if size == (w, h):
        return img
    return np.asarray(Image.fromarray(img).resize(size, Image.BILINEAR))


class SessionRecorder:
    def __init__(self, fly, path: str | Path | None = None, fps: float = FPS,
                 body_every_ms: int = BODY_EVERY_MS, video_scale: float = VIDEO_SCALE, info: dict | None = None):
        self.path = Path(path) if path else RUNS / f"oturum-{time.strftime('%Y%m%d-%H%M%S')}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.fly = fly
        self.t0 = fly.brain.time_ms
        self.body_every = int(body_every_ms)
        self.frame_every = int(round(1000 / fps))
        self.fps = fps
        self.video_scale = video_scale
        self.info = info or {}
        self.events: list[dict] = []
        self._offsets = [0]
        self._spikes: list[np.ndarray] = []
        self._n = 0
        self._body_t: list[float] = []
        self._qpos: list[np.ndarray] = []
        self._mocap: list[np.ndarray] = []
        self._held: list[bool] = []
        self._frame_t: list[float] = []
        self._writers: dict[str, object] = {}
        self._shapes: dict[str, tuple[int, int]] = {}
        self._placed = len(fly.repositions)
        self.closed = False
        fly.recorder = self

    @property
    def now_ms(self) -> float:
        return float(self.fly.brain.time_ms - self.t0)

    def event(self, kind: str, **data) -> None:
        self.events.append({"t_ms": self.now_ms, "tur": kind, **data})

    def step(self, fly, counts: np.ndarray) -> None:
        idx = np.flatnonzero(counts)
        if len(idx) and counts[idx].max() > 1:
            idx = np.repeat(idx, counts[idx])
        self._spikes.append(idx.astype(np.uint32))
        self._n += len(idx)
        self._offsets.append(self._n)
        if len(fly.repositions) > self._placed:
            self._placed = len(fly.repositions)
            self.event("yerlestirme")
        k = len(self._offsets) - 1  # kaydın başından bu yana geçen ms
        if k % self.body_every == 0:
            self._body_t.append(float(k))
            self._qpos.append(fly.body.snapshot().astype(np.float32))
            d = fly.body.sim.mj_data
            self._mocap.append(np.concatenate([d.mocap_pos, d.mocap_quat], axis=1).astype(np.float32))
            self._held.append(bool(fly.held))
        if k % self.frame_every == 0:
            self._frame_t.append(float(k))
            self._write("ekran", fly.feed.frame() if fly.feed is not None else None)
            eyes = fly.eyes.last_frames if fly.eyes is not None else {}
            self._write("gozler", np.concatenate([eyes["L"], eyes["R"]], axis=1) if eyes else None)

    def _write(self, name: str, frame: np.ndarray | None) -> None:
        if frame is None:
            if name not in self._shapes:
                return
            # Görüntü yoksa siyah kare. _shapes ölçeklenmiş boyutu tuttuğu için yeniden
            # ölçeklenmez; yoksa kare küçülür ve video yazıcı "boyutlar farklı" der.
            frame = np.zeros(self._shapes[name] + (3,), np.uint8)
        else:
            frame = _even(frame, self.video_scale)
        if name not in self._writers:
            if len(self._frame_t) > 1:  # ilk görüntü geç geldiyse önceki kareleri siyahla doldur
                blank = np.zeros_like(frame)
                self._writers[name] = self._open(name)
                for _ in range(len(self._frame_t) - 1):
                    self._writers[name].append_data(blank)
            else:
                self._writers[name] = self._open(name)
            self._shapes[name] = frame.shape[:2]
        self._writers[name].append_data(frame)

    def _open(self, name: str):
        return imageio.get_writer(self.path / f"{name}.mp4", fps=self.fps, macro_block_size=1,
                                  quality=8, ffmpeg_log_level="error")

    def close(self) -> Path:
        if self.closed:
            return self.path
        self.closed = True
        if self.fly.recorder is self:
            self.fly.recorder = None
        for w in self._writers.values():
            w.close()
        n_ms = len(self._offsets) - 1
        np.savez_compressed(self.path / "spikes.npz", ofset=np.array(self._offsets, np.uint32),
                            noron=np.concatenate(self._spikes) if self._spikes else np.zeros(0, np.uint32))
        np.savez_compressed(self.path / "govde.npz", t_ms=np.array(self._body_t), qpos=np.array(self._qpos),
                            mocap=np.array(self._mocap), tutuluyor=np.array(self._held))
        np.savez(self.path / "kareler.npz", t_ms=np.array(self._frame_t))
        (self.path / "olaylar.json").write_text(json.dumps(self.events, ensure_ascii=False, indent=1, default=float))
        meta = {
            "sure_ms": n_ms,
            "baslangic_beyin_ms": float(self.t0),
            "noron_sayisi": int(self.fly.conn.n),
            "spike_sayisi": int(self._n),
            "govde_araligi_ms": self.body_every,
            "kare_araligi_ms": self.frame_every,
            "kare_hizi": self.fps,
            "videolar": {k: {"yukseklik": v[0], "genislik": v[1]} for k, v in self._shapes.items()},
            "nq": int(self.fly.body.sim.mj_model.nq),
            "yeniden_yerlestirme": sum(e["tur"] == "yerlestirme" for e in self.events),
            **self.info,
        }
        (self.path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        return self.path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def load(path: str | Path) -> dict:
    """Kaydı okur: meta, olaylar, govde, spikes, kareler."""
    path = Path(path)
    out = {"yol": path, "meta": json.loads((path / "meta.json").read_text()),
           "olaylar": json.loads((path / "olaylar.json").read_text())}
    for name in ("govde", "spikes", "kareler"):
        with np.load(path / f"{name}.npz") as z:
            out[name] = {k: z[k] for k in z.files}
    return out


def spikes_between(rec: dict, t0_ms: float, t1_ms: float) -> np.ndarray:
    """[t0, t1) aralığında ateşleyen nöron indeksleri (tekrarlı; her spike bir kez)."""
    off = rec["spikes"]["ofset"]
    a, b = int(max(0, t0_ms)), int(min(len(off) - 1, t1_ms))
    return rec["spikes"]["noron"][off[a]:off[b]] if b > a else np.zeros(0, np.uint32)
