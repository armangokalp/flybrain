"""Bağ: sinek ekrana kilitli (K-040).

Gerçek sinek deneylerinin standart düzeni: hayvanın göğsüne (notum) ince bir iğne
yapıştırılır, iğne sabit bir kola tutturulur, önüne ekran konur. Sinek bacaklarını,
kanatlarını, başını serbestçe oynatır; kaçış devresi ateşlediğinde kaçış hareketini
yapar ama **gidemez**. Burada da öyle: tek çıkış yolu ekrandaki akışı kaydırmak.

Fizik: göğüs, dünyada duran bir tutucuya `weld` kısıtıyla bağlanır. Kısıt
kusursuz rijit değil — gerçek bir tungsten iğne de yapışkanıyla birlikte esner.
Esnekliğin ölçüsü `timeconst_s` (MuJoCo `solref`). Bu sayı keyfi değil, bir ölçütü var:

  - Sinek dinlenirken göğsün oynaması, "görünür hareket" eşiğinin (0,1 mm,
    body/confirm.py) ALTINDA kalmalı — yoksa kıpırdamayan sinek kaçmış sayılır.
  - Gerçek bir kaçış girişiminde göğsün yükselmesi o eşiği AŞMALI — yoksa sinek
    korksa bile "çıkış" kararı gövde onayından geçemez ve korku kararlara hiç
    yansımaz (K-032).

Ölçüm ve seçilen değer: docs/09-govde.md 18.

Bağ görünür: göğsün üstünde yapışkan damlası, ondan yukarı çıkan iğne ve iğneyi tutan
kol. Hepsi tutucunun (mocap gövde) üstünde durur; kütlesi ve çarpışması yoktur, yani
sineğin fiziğine dokunmaz. Sinek bağa yüklendiğinde göğsü yapışkan damlasının içinde
biraz kayar; çırpınma videoda buradan görülür.
"""

from dataclasses import dataclass

import mujoco as mj
import numpy as np

TETHER_BODY = "tutucu"
TETHER_EQ = "bag"

# Göğüs çerçevesinde iğnenin yapıştığı nokta (notumun tepesi; göğüs ağı z ≤ 0,44 mm).
NOTUM_MM = (-0.45, 0.0, 0.38)
PIN_RADIUS_MM = 0.035
PIN_LENGTH_MM = 2.4
GLUE_SIZE_MM = (0.26, 0.22, 0.12)
ARM_RADIUS_MM = 0.09
ARM_LENGTH_MM = 2.6     # iğnenin tepesinden geriye uzanan kol
PIN_RGBA = (0.30, 0.31, 0.34, 1.0)
GLUE_RGBA = (0.78, 0.56, 0.18, 1.0)
ARM_RGBA = (0.22, 0.23, 0.26, 1.0)


@dataclass(frozen=True)
class TetherConfig:
    """Bağın esnekliği ve görünürlüğü."""

    timeconst_s: float = 0.002   # MuJoCo solref zaman sabiti; ölçümle seçildi (docs/09-govde.md 18)
    dampratio: float = 1.0
    torque_scale: float = 1.0    # dönmeyi tutan kısmın ağırlığı (1: konumla aynı)
    visible: bool = True         # iğne ve kol çizilsin mi


def add_to_world(spec: mj.MjSpec, fly_name: str, cfg: TetherConfig) -> None:
    """Dünyaya tutucuyu ve göğse giden weld kısıtını ekler (derlemeden önce, sinek eklendikten sonra).

    Kısıt **kapalı** başlar: sinek önce kendi pasif duruşuna oturur, bağ ondan sonra
    takılır (`Tether.attach`). Gerçek düzende de hayvan önce yerleştirilir.
    """
    body = spec.worldbody.add_body(name=TETHER_BODY, mocap=True)
    if cfg.visible:
        x, y, z = NOTUM_MM
        g = body.add_geom(type=mj.mjtGeom.mjGEOM_ELLIPSOID, pos=[x, y, z],
                          size=list(GLUE_SIZE_MM), rgba=list(GLUE_RGBA))
        g.contype, g.conaffinity, g.mass, g.group = 0, 0, 0.0, 0
        g = body.add_geom(type=mj.mjtGeom.mjGEOM_CAPSULE,
                          fromto=[x, y, z, x, y, z + PIN_LENGTH_MM],
                          size=[PIN_RADIUS_MM, 0, 0], rgba=list(PIN_RGBA))
        g.contype, g.conaffinity, g.mass, g.group = 0, 0, 0.0, 0
        top = z + PIN_LENGTH_MM
        g = body.add_geom(type=mj.mjtGeom.mjGEOM_CAPSULE,
                          fromto=[x, y, top, x - ARM_LENGTH_MM, y, top],
                          size=[ARM_RADIUS_MM, 0, 0], rgba=list(ARM_RGBA))
        g.contype, g.conaffinity, g.mass, g.group = 0, 0, 0.0, 0

    eq = spec.add_equality()
    eq.name = TETHER_EQ
    eq.type = mj.mjtEq.mjEQ_WELD
    eq.objtype = mj.mjtObj.mjOBJ_BODY
    eq.name1 = TETHER_BODY                  # body1: tutucu
    eq.name2 = f"{fly_name}/c_thorax"       # body2: göğüs, tutucunun çerçevesine kilitlenir
    # [dayanak(3), göreli konum(3), göreli yön(4), tork ölçeği(1)]; birim göreli poz:
    # göğsün çerçevesi tutucunun çerçevesiyle çakışır.
    eq.data = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, cfg.torque_scale]
    eq.solref = [cfg.timeconst_s, cfg.dampratio]
    eq.active = False


class Tether:
    """Derlenmiş modeldeki bağ: takma, çözme, gerginlik ölçüsü."""

    def __init__(self, sim, fly_name: str, cfg: TetherConfig, thorax_body: str = "c_thorax"):
        self.sim = sim
        self.cfg = cfg
        m = sim.mj_model
        self._eq = mj.mj_name2id(m, mj.mjtObj.mjOBJ_EQUALITY, TETHER_EQ)
        if self._eq < 0:
            raise RuntimeError("bağ kısıtı modelde yok")
        self._thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{fly_name}/{thorax_body}")
        self._mocap = m.body_mocapid[mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, TETHER_BODY)]

    @property
    def attached(self) -> bool:
        return bool(self.sim.mj_data.eq_active[self._eq])

    def attach(self) -> None:
        """Bağı göğsün **o anki** duruşuna takar: tutucu oraya taşınır, kısıt açılır."""
        m, d = self.sim.mj_model, self.sim.mj_data
        mj.mj_kinematics(m, d)
        d.mocap_pos[self._mocap] = d.xpos[self._thorax]
        d.mocap_quat[self._mocap] = d.xquat[self._thorax]
        d.eq_active[self._eq] = 1
        mj.mj_forward(m, d)

    def release(self) -> None:
        """Bağı çözer (deneyler için)."""
        self.sim.mj_data.eq_active[self._eq] = 0

    @property
    def anchor(self) -> np.ndarray:
        """Tutucunun tuttuğu nokta (mm)."""
        return self.sim.mj_data.mocap_pos[self._mocap].copy()

    @property
    def strain_mm(self) -> float:
        """Göğsün tutucudan kaçtığı mesafe: bağın o anki gerginliği."""
        d = self.sim.mj_data
        return float(np.linalg.norm(d.xpos[self._thorax] - d.mocap_pos[self._mocap]))
