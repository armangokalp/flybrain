"""Sineğin kendi gözleriyle görme: 3D sahne → göz kolonları → görme nöronları.

Her göz için başa bağlı bir kamera (FlyGym, 157° görüş açısı) sahneyi çizer. Görüntü
FlyGym'in 721 ommatidyumuna indirgenmez; bunun yerine konnektomdaki her kolon
nöronunun kendi bakış yönünden örneklenir (senses/eye.py: kolon → φ, θ):

  1. Kolonun baş çerçevesindeki yönü: x ileri, y sol, z yukarı.
     d = (cos θ · sin φ, ±cos θ · cos φ, sin θ); + sol göz, − sağ göz.
  2. Her karede baş ve kamera yönelimi fizikten okunur; yön kameranın düz (rectilinear)
     görüntüsüne izdüşürülür. Balık gözü düzeltmesine gerek kalmaz.
  3. Ommatidyumun kabul açısı (5°, yarı yükseklikte tam genişlik) yedi noktalı bir
     örnekle uygulanır: merkez ve 2,5° uzaktaki altı nokta, Gauss ağırlıklı.
  4. Zamansal kodlama: her kolon kendi parlaklığına uyum sağlar (yerel ışık adaptasyonu,
     ADAPT_MS). Kontrast, kolonun uyum sağladığı parlaklığa göre alınır. Geçici hücreler
     (L2, Mi1, Tm3) bu kontrastın yüksek geçiren süzgeçten geçmiş halini, kalıcı hücreler
     (L3) kontrastın kendisini görür. Sonuç Faz 3'teki kodlamayla (senses/vision.py)
     Poisson hızına çevrilir.

Durağan bir sahne böylece zamanla sönümlenir; değişen, hareket eden ya da yaklaşan şeyler
yanıt üretir. Faz 3'teki durağan kodlama (tüm görüntünün ortalamasına göre sürekli kontrast)
gövdeli sinekte durağan sahneyi sürekli bir uyarıma çeviriyordu ve dev lif (DNp01) hiçbir
şey hareket etmezken 63 Hz ateşliyordu.

Baş hareket ederse (boyun kasları) görüntü de onunla döner. Kameranın görmediği kolonlar
(çok arkaya ya da çok aşağıya bakanlar) kontrast üretmez.
"""

import mujoco as mj
import numba as nb
import numpy as np

from flybrain.connectome.connectome import Connectome
from flybrain.senses.eye import Eye
from flybrain.senses.vision import (
    ACCEPTANCE_DEG, LUM_WEIGHTS, VisionConfig, contrast_to_stimulus, neuron_groups,
)
from flybrain.sim.stimulus import Stimulus

EYE_CAMERAS = {"L": "l_eye_cam_camera", "R": "r_eye_cam_camera"}
# Yerel ışık adaptasyonunun zaman sabiti (VARSAYIM; fotoreseptör ve lamina adaptasyonu
# "saniyeler içinde": Nikolaev ve ark. 2009).
ADAPT_MS = 1000.0
# Geçici hücrelerin yüksek geçiren süzgeci (VARSAYIM; yayımlanmış sayılara ulaşılamadı).
TRANSIENT_MS = 100.0
RENDER_HW = (512, 450)  # FlyGym'in göz kamerası çözünürlüğü
_RING = 6


def _kernel() -> tuple[np.ndarray, np.ndarray]:
    """Yedi noktalı kabul açısı örneği: (açısal kaymalar [derece, (7, 2)], ağırlıklar)."""
    r = ACCEPTANCE_DEG / 2
    ang = np.linspace(0, 2 * np.pi, _RING, endpoint=False)
    offsets = np.r_[[[0.0, 0.0]], np.c_[r * np.cos(ang), r * np.sin(ang)]]
    sigma = ACCEPTANCE_DEG / 2.355
    w = np.exp(-(offsets ** 2).sum(axis=1) / (2 * sigma ** 2))
    return offsets, w / w.sum()


@nb.njit(cache=True)
def _sample_eye(dirs, M, focal, img, scale, weights, out_rgb, out_wsum):
    """Bir gözün bütün kolonları: izdüşüm, bilineer örnekleme, kabul açısı ağırlıklı ortalama.

    dirs: (k, m, 3) baş çerçevesi yönleri; M: baş → kamera dönüşümü (v = d @ M);
    img: (H, W, 3) kare, değerler × scale = [0, 1]. Çıktı: out_rgb (m, 3), out_wsum (m,).
    """
    k, m, _ = dirs.shape
    H, W = img.shape[0], img.shape[1]
    for j in range(m):
        sw = 0.0
        r = 0.0
        g = 0.0
        b = 0.0
        for q in range(k):
            dx = dirs[q, j, 0]
            dy = dirs[q, j, 1]
            dz = dirs[q, j, 2]
            vx = dx * M[0, 0] + dy * M[1, 0] + dz * M[2, 0]
            vy = dx * M[0, 1] + dy * M[1, 1] + dz * M[2, 1]
            depth = -(dx * M[0, 2] + dy * M[1, 2] + dz * M[2, 2])
            if depth <= 1e-3:
                continue
            x = W / 2 + focal * vx / depth
            y = H / 2 - focal * vy / depth
            if x < 0 or x > W - 1 or y < 0 or y > H - 1:
                continue
            x0 = min(int(x), W - 2)
            y0 = min(int(y), H - 2)
            fx = x - x0
            fy = y - y0
            w = weights[q]
            sw += w
            for ch in range(3):
                val = ((img[y0, x0, ch] * (1 - fx) + img[y0, x0 + 1, ch] * fx) * (1 - fy)
                       + (img[y0 + 1, x0, ch] * (1 - fx) + img[y0 + 1, x0 + 1, ch] * fx) * fy)
                if ch == 0:
                    r += w * val
                elif ch == 1:
                    g += w * val
                else:
                    b += w * val
        out_wsum[j] = sw
        norm = scale / max(sw, 1e-9)
        out_rgb[j, 0] = r * norm
        out_rgb[j, 1] = g * norm
        out_rgb[j, 2] = b * norm


def head_directions(side: np.ndarray, phi_deg: np.ndarray, theta_deg: np.ndarray) -> np.ndarray:
    phi, theta = np.radians(phi_deg), np.radians(theta_deg)
    lateral = np.where(np.asarray(side) == "L", 1.0, -1.0)
    return np.c_[np.cos(theta) * np.sin(phi), lateral * np.cos(theta) * np.cos(phi), np.sin(theta)]


class FlyEyes:
    def __init__(self, sim, fly_name: str, head_body: str, conn: Connectome,
                 config: VisionConfig, eye: Eye | None = None):
        self.sim = sim
        self.cfg = config
        m = sim.mj_model
        self._head = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{fly_name}/{head_body}")
        self._cams = {s: mj.mj_name2id(m, mj.mjtObj.mjOBJ_CAMERA, f"{fly_name}/{c}") for s, c in EYE_CAMERAS.items()}
        if min(self._cams.values()) < 0:
            raise ValueError("göz kameraları yok; gövde add_vision() ile kurulmalı")
        self._focal = {s: (RENDER_HW[0] / 2) / np.tan(np.radians(m.cam_fovy[c]) / 2) for s, c in self._cams.items()}
        self.renderer = mj.Renderer(m, *RENDER_HW)
        self._option = mj.MjvOption()
        self._option.geomgroup[1] = 0  # yardımcı işaretler
        self._option.geomgroup[2] = 0  # gözün kendini görmemesi için gizlenen gövde parçaları

        eye = eye or Eye(conn)
        groups, tonic = neuron_groups(conn, config.mode)
        offsets, self._weights = _kernel()
        self.groups = []       # (ad, nöronlar, kanal, kutup, dinamik)
        self._group_dirs = []  # ((7, n, 3) baş çerçevesi yönleri, taraf)
        for name, idx, channel, polarity, dynamics in groups:
            kept, side, phi, theta = eye.neuron_directions(idx)
            self.groups.append((name, kept, channel, polarity, dynamics))
            dirs = np.stack([head_directions(side, phi + dp, theta + dt) for dp, dt in offsets])
            self._group_dirs.append((dirs, side))
        self.bias_mv = None
        if tonic:
            self.bias_mv = np.zeros(conn.n)
            self.bias_mv[np.concatenate(tonic)] = config.tonic_mv
        self.input_neurons = np.unique(np.concatenate([g[1] for g in self.groups] + tonic))
        # Her göz için bütün grupların yönleri tek dizide: bir karede tek izdüşüm ve tek örnekleme.
        self._eye_dirs = {}
        for s in self._cams:
            parts = [(k, np.flatnonzero(side == s)) for k, (_, side) in enumerate(self._group_dirs)]
            dirs = np.ascontiguousarray(np.concatenate([self._group_dirs[k][0][:, sel] for k, sel in parts], axis=1))
            self._eye_dirs[s] = (dirs, parts)
        self.last_frames: dict[str, np.ndarray] = {}
        self.last_samples: dict[str, np.ndarray] = {}
        self.last_contrast: dict[str, np.ndarray] = {}
        self.reset()

    def reset(self):
        """Uyum durumunu siler; bir sonraki kare "zaten bakılan" sahne sayılır."""
        self._adapted: dict[str, np.ndarray] = {}
        self._lowpass: dict[str, np.ndarray] = {}

    def render(self, as_float: bool = True) -> dict[str, np.ndarray]:
        """İki gözün karesi: as_float ise [0, 1] aralığında float, değilse uint8.

        last_frames her zaman uint8 kareleri tutar.
        """
        d = self.sim.mj_data
        frames = {}
        for s, cam in self._cams.items():
            self.renderer.update_scene(d, cam, scene_option=self._option)
            frames[s] = self.renderer.render()
        self.last_frames = frames
        if as_float:
            return {s: f.astype(np.float64) / 255.0 for s, f in frames.items()}
        return frames

    def column_values(self, frames: dict[str, np.ndarray] | None = None) -> dict[str, dict[str, np.ndarray]]:
        """Grup ve kanal başına kolon değerleri; kameranın dışında kalanlar NaN."""
        frames = frames or self.render(as_float=False)
        d = self.sim.mj_data
        R_head = d.xmat[self._head].reshape(3, 3)
        out = {g[0]: {c: np.full(len(g[1]), np.nan) for c in ("lum", "green", "blue")} for g in self.groups}
        for s, cam in self._cams.items():
            dirs, parts = self._eye_dirs[s]
            if dirs.shape[1] == 0:
                continue
            img = frames[s]
            if img.shape[:2] != RENDER_HW:
                raise ValueError(f"göz karesi {RENDER_HW} boyutunda olmalı")
            M = R_head.T @ d.cam_xmat[cam].reshape(3, 3)  # baş → kamera çerçevesi
            mean_rgb = np.empty((dirs.shape[1], 3))
            wsum = np.empty(dirs.shape[1])
            scale = 1.0 / 255.0 if img.dtype == np.uint8 else 1.0
            _sample_eye(dirs, M, self._focal[s], img, scale, self._weights, mean_rgb, wsum)
            hidden = wsum <= 0.5
            vals = {"lum": mean_rgb @ LUM_WEIGHTS, "green": mean_rgb[:, 1], "blue": mean_rgb[:, 2]}
            start = 0
            for k, sel in parts:
                name = self.groups[k][0]
                for c, val in vals.items():
                    col = val[start:start + len(sel)].copy()
                    col[hidden[start:start + len(sel)]] = np.nan
                    out[name][c][sel] = col
                start += len(sel)
        return out

    def encode(self, dt_ms: float, frames: dict[str, np.ndarray] | None = None) -> Stimulus:
        """Yeni kareyi kodlar; dt_ms önceki kareden bu yana geçen süre."""
        values = self.column_values(frames)
        k_adapt = 1.0 - np.exp(-dt_ms / ADAPT_MS)
        k_fast = 1.0 - np.exp(-dt_ms / TRANSIENT_MS)
        contrast = {}
        for name, _, channel, _, dynamics in self.groups:
            x = values[name][channel]
            vis = np.isfinite(x)
            if name not in self._adapted:
                self._adapted[name] = x.copy()
                self._lowpass[name] = np.zeros(len(x))
            a = self._adapted[name]
            fresh = vis & ~np.isfinite(a)
            a[fresh] = x[fresh]
            c = np.zeros(len(x))
            c[vis] = (x[vis] - a[vis]) / np.maximum(a[vis], 1e-3)
            a[vis] += (x[vis] - a[vis]) * k_adapt
            if dynamics == "gecici":
                lp = self._lowpass[name]
                out = c - lp
                lp += (c - lp) * k_fast
                c = out
            contrast[name] = c
        self.last_samples = {name: values[name]["lum"] for name, *_ in self.groups}
        self.last_contrast = contrast
        return contrast_to_stimulus(self.cfg, [(g[0], g[1], g[3]) for g in self.groups], contrast)

    def close(self):
        self.renderer.close()
