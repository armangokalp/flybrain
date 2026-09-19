"""Kayıttan gövdeyi yeniden kurar ve istenen açıdan çizer (Faz 6).

Gövde kaydın qpos'undan kurulur (mj_forward); fizik çalışmaz. Telefon ekranının çarpışması
olmadığı için yalnızca çizimde saydam yapılabilir; sineği çoğu açıdan ekranın arkası kapatıyor.
"""

from pathlib import Path

import mujoco as mj
import numpy as np

from flybrain.viz.record import load

SCREEN_BODY = "ekran"


class Replay:
    def __init__(self, rec: dict | str | Path, width: int = 640, height: int = 480):
        from flybrain.body.body import Body
        from flybrain.body.scene import SceneConfig
        from flybrain.body.tether import TetherConfig

        self.rec = rec if isinstance(rec, dict) else load(rec)
        # Bağlı oturumda (K-040) tutucu da fizik dışı bir gövde: kayıtta iki mocap satırı var
        # ve model onu tanımazsa kayıt yüklenemiyor. Eski kayıtlarda alan yok, sinek serbest.
        bagli = bool(self.rec["meta"].get("bagli", False))
        self.body = Body(scene=SceneConfig(), tether=TetherConfig() if bagli else None)
        self.m, self.d = self.body.sim.mj_model, self.body.sim.mj_data
        g = self.rec["govde"]
        if g["qpos"].shape[1] != self.m.nq:
            raise ValueError(f"kayıttaki durum vektörü ({g['qpos'].shape[1]}) modelle ({self.m.nq}) uyuşmuyor")
        self.t_ms, self.qpos, self.held = g["t_ms"], g["qpos"], g["tutuluyor"]
        self.mocap = g.get("mocap")  # telefon ekranının konumu; eski kayıtlarda yok
        self.renderer = mj.Renderer(self.m, height, width)
        self.camera = mj.MjvCamera()
        self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.camera.distance, self.camera.elevation, self.camera.azimuth = 5.5, -20.0, 135.0
        body_name = lambda g_: mj.mj_id2name(self.m, mj.mjtObj.mjOBJ_BODY, self.m.geom_bodyid[g_]) or ""
        self._screen = [g_ for g_ in range(self.m.ngeom) if body_name(g_) == SCREEN_BODY]
        self._thorax = mj.mj_name2id(self.m, mj.mjtObj.mjOBJ_BODY, f"{self.body.fly.name}/c_thorax")

    @property
    def duration_ms(self) -> float:
        return float(self.t_ms[-1])

    def index(self, t_ms: float) -> int:
        return int(np.clip(np.searchsorted(self.t_ms, t_ms, side="right") - 1, 0, len(self.t_ms) - 1))

    def pose(self, t_ms: float) -> int:
        """Gövdeyi t_ms'deki (ya da hemen önceki) kayıtlı duruşa koyar."""
        i = self.index(t_ms)
        self.set_state(i)
        self.d.qvel[:] = 0.0
        mj.mj_forward(self.m, self.d)
        return i

    def set_state(self, i: int) -> None:
        self.d.qpos[:] = self.qpos[i]
        if self.mocap is not None:
            self.d.mocap_pos[:] = self.mocap[i, :, :3]
            self.d.mocap_quat[:] = self.mocap[i, :, 3:]

    def thorax(self) -> np.ndarray:
        return self.d.xpos[self._thorax].copy()

    def upright(self) -> float:
        return float(self.d.xmat[self._thorax][8])

    def render(self, t_ms: float, hide_screen: bool = True, follow: bool = True) -> np.ndarray:
        self.pose(t_ms)
        if follow:
            self.camera.lookat[:] = self.thorax()
        saved = self.m.geom_rgba.copy(), self.m.mat_rgba.copy()
        if hide_screen:
            for g in self._screen:
                self.m.geom_rgba[g, 3] = 0.0
                if self.m.geom_matid[g] >= 0:
                    self.m.mat_rgba[self.m.geom_matid[g], 3] = 0.0
        self.renderer.update_scene(self.d, self.camera)
        img = self.renderer.render()
        self.m.geom_rgba[:], self.m.mat_rgba[:] = saved
        return img

    def body_frames(self) -> dict[str, np.ndarray]:
        """Her kayıtlı duruş için bütün gövde parçalarının konumu ve yönü (xpos, xquat)."""
        pos = np.zeros((len(self.t_ms), self.m.nbody, 3), np.float32)
        quat = np.zeros((len(self.t_ms), self.m.nbody, 4), np.float32)
        for i in range(len(self.t_ms)):
            self.set_state(i)
            mj.mj_kinematics(self.m, self.d)
            pos[i], quat[i] = self.d.xpos, self.d.xquat
        return {"pos": pos, "quat": quat}

    def close(self) -> None:
        self.renderer.close()
        self.body.close()
