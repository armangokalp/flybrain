"""NeuroMechFly gövdesi: pasif eklem özellikleri, eklem sınırları, tork aktüatörleri.

Gövdeyi hareket ettiren tek şey `step(torques)` ile verilen torklardır; bu torklar
yalnızca kas modelinden (motor nöron spike'larından) gelir.
"""

from dataclasses import dataclass

import mujoco as mj
import numpy as np

from flybrain.body.muscles import LEGS, load_geometry
from flybrain.body.scene import Scene, SceneConfig, add_to_world
from flybrain.body.tether import Tether, TetherConfig
from flybrain.body.tether import add_to_world as add_tether

# Bacak eklemleri: kas-iskelet modelinin pasif özellikleri (kas kuvvetleriyle birlikte
# kullanılan değerler). Kütle eylemsizliği NeuroMechFly'ınki gibi küçük tutulur; küçük
# uzuvlarda hareketi pasif sertlik ve sönüm belirler.
LEG_ARMATURE = 1e-6
# Diğer eklemler: NeuroMechFly varsayılanları.
OTHER_STIFFNESS = 10.0
OTHER_DAMPING = 0.5
OTHER_ARMATURE = 1e-6
TORQUE_LIMIT = 500.0      # µN·mm; yalnızca sayısal güvenlik sınırı, TTM torkunun üstünde
TARSUS_RANGE = 0.6        # rad, nötr açının iki yanı (VARSAYIM)
TIMESTEP_S = 1e-4
# Eklem sınırlarının tepki süresi (MuJoCo solref). Varsayılan 20 ms, küçük uzuvlarda kas
# torkları karşısında sınırın aşılmasına izin veriyor; zaman adımının 5 katına indirildi.
LIMIT_TIMECONST_S = 5e-4

LEG_KEYS = ("coxa_yaw", "coxa_pitch", "coxa_roll", "trochanter_pitch", "trochanter_roll", "tibia_pitch")


def _leg_joint(leg: str, key: str) -> str:
    return {
        "coxa_yaw": f"c_thorax-{leg}_coxa-yaw",
        "coxa_pitch": f"c_thorax-{leg}_coxa-pitch",
        "coxa_roll": f"c_thorax-{leg}_coxa-roll",
        "trochanter_pitch": f"{leg}_coxa-{leg}_trochanterfemur-pitch",
        "trochanter_roll": f"{leg}_coxa-{leg}_trochanterfemur-roll",
        "tibia_pitch": f"{leg}_trochanterfemur-{leg}_tibia-pitch",
    }[key]


def is_leg_dof(name: str) -> bool:
    return any(name.startswith(f"{leg}_") or f"-{leg}_" in name for leg in LEGS)


@dataclass
class BodyState:
    time_s: float
    thorax_pos: np.ndarray        # mm
    thorax_quat: np.ndarray
    joint_angles: np.ndarray      # rad, dofs sırasıyla
    joint_velocities: np.ndarray  # rad/s


class Body:
    """3D sinek gövdesi ve dünyası: düz zemin; istenirse gri arena ve telefon ekranı (body/scene.py).

    `tether` verilirse sinek ekrana kilitlidir: göğsü dünyada duran bir tutucuya bağlanır
    (body/tether.py, K-040). Bacaklar, kanatlar ve baş serbest kalır.
    """

    def __init__(self, camera_res: tuple[int, int] = (360, 480), scene: SceneConfig | None = None,
                 tether: "TetherConfig | None" = None):
        from flygym import Simulation
        from flygym.anatomy import ActuatedDOFPreset, AxisOrder, JointPreset, Skeleton
        from flygym.compose import ActuatorType, FlatGroundWorld, KinematicPosePreset, NeuroMechFly
        from flygym.utils.math import Rotation3D

        self.geom = load_geometry()
        self.passive = {"leg": self.geom["passive"]["stiffness"], "other": OTHER_STIFFNESS}
        fly = NeuroMechFly(name="sinek")
        skel = Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.ALL_BIOLOGICAL)
        fly.add_joints(skel, neutral_pose=KinematicPosePreset.NEUTRAL,
                       stiffness=OTHER_STIFFNESS, damping=OTHER_DAMPING, armature=OTHER_ARMATURE)
        self._set_leg_passive(fly)
        dofs = fly.skeleton.get_actuated_dofs_from_preset(ActuatedDOFPreset.ALL)
        fly.add_actuators(dofs, actuator_type=ActuatorType.MOTOR, forcerange=(-TORQUE_LIMIT, TORQUE_LIMIT))
        fly.colorize()
        fly.add_vision()  # başa bağlı iki göz kamerası (body/sight.py)
        self.camera = fly.add_tracking_camera(name="izleme")
        self.side_camera = fly.add_tracking_camera(
            name="yan", pos_offset=(0.0, -6.0, 0.8),
            rotation=Rotation3D("xyaxes", (1, 0, 0, 0, 0.1, 1)),
        )
        fly.add_leg_adhesion()
        world = FlatGroundWorld()
        if scene is not None:
            add_to_world(world.mjcf_root, scene)
        world.add_fly(fly, [0, 0, 0.7], Rotation3D(format="quat", values=[1, 0, 0, 0]))
        if tether is not None:
            add_tether(world.mjcf_root, fly.name, tether)
        self.fly = fly
        self.sim = Simulation(world, timestep=TIMESTEP_S)
        self._motor = ActuatorType.MOTOR
        self.dofs = [d.name for d in fly.get_actuated_jointdofs_order(ActuatorType.MOTOR)]
        self.scene = Scene(self.sim, fly.name, scene) if scene is not None else None
        self.tether = Tether(self.sim, fly.name, tether) if tether is not None else None
        self._renderers: dict[str, mj.Renderer] = {}
        self.camera_res = camera_res
        self.reset()

    def _set_leg_passive(self, fly):
        k = self.geom["passive"]["stiffness"]
        c = self.geom["passive"]["damping"]
        front = self.geom["front_leg_ranges"]
        neutral = self.geom["nmf"]["neutral_angles"]
        for dof, joint in fly.jointdof_to_mjcfjoint.items():
            name = dof.name
            if not is_leg_dof(name):
                continue
            joint.stiffness = [k, 0.0, 0.0]
            joint.damping = [c, 0.0, 0.0]
            joint.armature = LEG_ARMATURE
            lo = hi = None
            for leg in LEGS:
                for key in LEG_KEYS:
                    if name == _leg_joint(leg, key):
                        # Ön bacağın anatomik aralığı, nötr açıya göre kaydırılarak her bacağa
                        # uygulanır (VARSAYIM: bacakların yapısal benzerliği).
                        r = front[key]["range"]
                        ref = neutral[_leg_joint("lf", key)]
                        lo = neutral[name] + (r[0] - ref)
                        hi = neutral[name] + (r[1] - ref)
            if name.endswith("tarsus1-pitch"):
                lo, hi = neutral[name] - TARSUS_RANGE, neutral[name] + TARSUS_RANGE
            if lo is not None:
                joint.limited = mj.mjtLimited.mjLIMITED_TRUE
                joint.range = [min(lo, hi), max(lo, hi)]
                joint.solref_limit = [LIMIT_TIMECONST_S, 1.0]

    def reset(self):
        # sim.reset() bağı da çözer (eq_active → eq_active0). Sinek önce kendi pasif duruşuna
        # oturur, bağ ondan sonra takılır (EmbodiedFly.reset → Tether.attach).
        self.sim.reset()
        self.sim.set_leg_adhesion_states(self.fly.name, np.ones(6))
        self.sim.mj_data.qfrc_applied[:] = 0.0
        self._zero = np.zeros(len(self.dofs))
        if self.scene is not None:
            # Tam sıfırlama: sinek başlangıç noktasına döndüğü için ekran da yeniden yerleşir
            # (hep aynı yere). Deneycinin yeniden yerleştirmesi bunu yapmaz (K-038).
            self.scene.snap(force=True)

    def upright(self) -> float:
        """Göğsün dikey ekseninin dünya dikeyiyle kosinüsü: 1 dik, < 0 sırtüstü."""
        d = self.sim.mj_data
        if not hasattr(self, "_thorax_id"):
            self._thorax_id = mj.mj_name2id(self.sim.mj_model, mj.mjtObj.mjOBJ_BODY, f"{self.fly.name}/c_thorax")
        return float(d.xmat[self._thorax_id][8])

    def _free_qpos(self) -> int:
        m = self.sim.mj_model
        return int(m.jnt_qposadr[list(m.jnt_type).index(mj.mjtJoint.mjJNT_FREE)])

    def snapshot(self) -> np.ndarray:
        """Gövde duruşunun kopyası (qpos)."""
        return self.sim.mj_data.qpos.copy()

    def hold(self, pose: np.ndarray) -> None:
        """Gövdeyi `pose` duruşunda sabit tutar (hızlar sıfır); her fizik adımından sonra çağrılır."""
        m, d = self.sim.mj_model, self.sim.mj_data
        d.qpos[:] = pose
        d.qvel[:] = 0.0
        d.qacc_warmstart[:] = 0.0
        mj.mj_forward(m, d)

    def place(self, pose: np.ndarray, yaw: float) -> None:
        """Deneyci müdahalesi: gövdeyi `pose` duruşuna koyar (hızlar sıfır).

        Göğsün yatay konumu olduğu yerde kalır; yüksekliği ve eğimi `pose`'tan gelir,
        yönü (düşey eksen etrafında) `yaw` olur.
        """
        m, d = self.sim.mj_model, self.sim.mj_data
        f = self._free_qpos()
        q = pose.copy()
        q[f:f + 2] = d.qpos[f:f + 2]
        w, x, y, z = pose[f + 3:f + 7]
        pose_yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        turn = np.array([np.cos((yaw - pose_yaw) / 2), 0.0, 0.0, np.sin((yaw - pose_yaw) / 2)])
        quat = np.zeros(4)
        mj.mju_mulQuat(quat, turn, pose[f + 3:f + 7])
        q[f + 3:f + 7] = quat
        d.qpos[:] = q
        d.qvel[:] = 0.0
        d.qacc_warmstart[:] = 0.0
        mj.mj_forward(m, d)

    @property
    def time_s(self) -> float:
        return float(self.sim.time)

    def step(self, torques: np.ndarray, n_steps: int = 1):
        self.sim.set_actuator_inputs(self.fly.name, self._motor, torques)
        for _ in range(n_steps):
            self.sim.step()

    def apply_external(self, torques: np.ndarray | None):
        """Dış kuvvet (deneycinin probu gibi): eklem sırasıyla tork; None temizler.

        Yalnızca deneylerde kullanılır; sineğin kendi hareketi kaslardan gelir.
        """
        if not hasattr(self, "_vadr"):
            self.dof_velocities()
        f = self.sim.mj_data.qfrc_applied
        f[:] = 0.0
        if torques is not None:
            f[self._vadr] = torques

    def _dof_joint_ids(self) -> np.ndarray:
        m = self.sim.mj_model
        return np.array([mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{self.fly.name}/{d}") for d in self.dofs])

    def dof_ranges(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Aktüatör sırasıyla eklem alt/üst sınırları ve sınırlı olup olmadıkları."""
        m = self.sim.mj_model
        ids = self._dof_joint_ids()
        return m.jnt_range[ids, 0].copy(), m.jnt_range[ids, 1].copy(), m.jnt_limited[ids].astype(bool)

    def dof_angles(self) -> np.ndarray:
        """Aktüatör sırasıyla eklem açıları."""
        if not hasattr(self, "_qadr"):
            self._qadr = self.sim.mj_model.jnt_qposadr[self._dof_joint_ids()]
        return self.sim.mj_data.qpos[self._qadr]

    def dof_velocities(self) -> np.ndarray:
        """Aktüatör sırasıyla eklem açısal hızları (rad/s)."""
        if not hasattr(self, "_vadr"):
            self._vadr = self.sim.mj_model.jnt_dofadr[self._dof_joint_ids()]
        return self.sim.mj_data.qvel[self._vadr]

    def state(self) -> BodyState:
        pos = self.sim.get_body_positions(self.fly.name)[0].copy()
        quat = self.sim.get_body_rotations(self.fly.name)[0].copy()
        return BodyState(
            time_s=self.time_s,
            thorax_pos=pos,
            thorax_quat=quat,
            joint_angles=self.sim.get_joint_angles(self.fly.name).copy(),
            joint_velocities=self.sim.get_joint_velocities(self.fly.name).copy(),
        )

    @property
    def joint_names(self) -> list[str]:
        return [d.name for d in self.fly.get_jointdofs_order()]

    def render(self, camera: str = "izleme") -> np.ndarray:
        if camera not in self._renderers:
            h, w = self.camera_res
            self._renderers[camera] = mj.Renderer(self.sim.mj_model, h, w)
            if self.scene is not None:
                self.scene.register(self._renderers[camera])
        r = self._renderers[camera]
        r.update_scene(self.sim.mj_data, camera=f"{self.fly.name}/{camera}")
        return r.render()

    def close(self):
        for r in self._renderers.values():
            r.close()
        self._renderers.clear()
