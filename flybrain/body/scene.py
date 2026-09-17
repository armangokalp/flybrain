"""Sahne: gri arena ve sineği izleyen telefon ekranı (K-021, K-028).

Ekran, sineğin önünde duran dikey bir telefondur:
  - Oran 9:19,5 (güncel akıllı telefonlar). Genişlik yay boyunca ölçülür.
  - Başın düşey ekseni etrafında kavisli: 180° genişlik, 2 mm yarıçap. Yükseklik orandan
    gelir (~13,6 mm).
  - Görüntü ekranın kendisidir; ışıktan etkilenmez (ışık yayan malzeme).
  - Fiziksel engel değildir (çarpışma yok); sinek içinden geçebilir.

Sinek ekranın yalnızca alt ~%60'ını görür: gözler zeminden 0,7 mm yüksekte, göz kolonlarının
en üstü ~75° yukarı bakıyor. Bu yüzden post görseli ekranın altında, gezinme çubuğunun hemen
üstünde durur (telefonda aşağı kaydırılmış akış; body/phone.py).

Telefon zemindeki bir yuvaya oturur: gezinme çubuğu ve alt çerçeve zeminin altında kalır, post
zemin hizasından başlar. Aksi halde gezinme çubuğu göz kolonlarının en yoğun olduğu ufuk
bandına düşüyor ve postu kolonların yalnızca %37'si görüyordu; yuvayla %62'si görüyor. Ekranı
yaklaştırmak da işe yarıyor (1 mm'de %66) ama ön bacak uçları başın ekseninden 1,35 mm
öteye uzandığı için bacaklar ekranın içinden geçiyor (docs/09-govde.md 11).

İzleme (K-021): ekranın ekseni başın konumunu, yönü göğsün yönünü gecikmeyle izler
(FOLLOW_MS). Hızlı hareketler (sıçrama, ani dönüş) görüntüyü bir an değiştirir; ekran sonra
yeniden sineğin önüne gelir. İzleme bir "dünya fiziği" kararıdır; sineğin kararlarına dokunmaz.

Arena gridir; gökyüzü ile zemin arasındaki kontrast düşük tutulur. Işık yukarıdan gelir
(yönlü ışık, gölgesiz). Kameraya bağlı ışık (MuJoCo'nun varsayılanı) zayıf tutulur: göz
kameralarında zeminin parlaklığı bakış açısına bağlı olmasın diye.

Ekran görüntüsü değiştiğinde doku modelde güncellenir ve bu sahneyi çizen her çiziciye
(göz kameraları, video kameraları) yeniden yüklenir.
"""

from dataclasses import dataclass

import mujoco as mj
import numpy as np

from flybrain.body.phone import post_box

PHONE_ASPECT = 19.5 / 9      # yükseklik / genişlik
SKY_GRAY = 0.5
FLOOR_GRAYS = (0.40, 0.45)   # zemin dokusunun iki karesi
BACK_GRAY = 0.15             # telefonun arkası
TOP_LIGHT = 0.6              # yukarıdan gelen ışığın gücü
HEADLIGHT = (0.3, 0.1)       # kameraya bağlı ışık: ortam, yayılı
EYE_HEIGHT_MM = 0.7          # oturmuş sineğin göz yüksekliği (ölçüm: 0,68-0,71)
SCREEN_BODY = "ekran"
SCREEN_TEXTURE = "ekran"
_ARC_SEGMENTS = 72


@dataclass(frozen=True)
class SceneConfig:
    # Ekran **dünyada duran bir nesne** (K-038). Önceden sineğin başını izliyordu, yani bir kask
    # gibiydi: 180°'lik ekran başa sarılıyor, postun üst üçte biri gözün %11'ini kaplıyordu.
    # Daraltmak bunu düzeltiyor ama kaçışı söndürüyor (ölçüm: LC4 154 → 3, sıçrama 3,24 → 0,04 mm),
    # çünkü yaklaşan disk de küçülüyor. Sabit nesnede mesafeyi sinek seçiyor: korkunca geri
    # çekiliyor (ölçülen kaçış yer değiştirmesi ~1,7-1,9 mm) ve postu daha geniş görüyor.
    #
    # Telefonun fiziksel boyu değişmedi (6,3 × 13,6 mm); sinek 2 mm yerine 2,5 mm uzakta
    # başlıyor ve ekran onu izlemiyor. Mesafe 3 tohumla ölçüldü (telefonun fiziksel boyu her mesafede aynı tutuldu):
    #
    #   mesafe   postun üstü/ortası/altı gözde      LC4   sıçrama   kaçış
    #    2,0 mm      %11,6 / %29,1 / %59,3           35    2,40 mm   2/3   (eski)
    #    2,5 mm      %12,3 / %38,2 / %49,5           48    1,32 mm   2/3   ← seçilen
    #    3,0 mm      %14,8 / %42,8 / %42,3           64    1,49 mm   1/3
    #    4,0 mm      %21,8 / %45,0 / %33,2           22    0,10 mm   0/3
    #    5,0 mm      %29,7 / %42,5 / %27,9           16    0,10 mm   0/3
    #
    # 2,5 mm: kaçış eskisiyle aynı, postun altının baskınlığı %59'dan %49'a iniyor. Daha uzakta
    # post daha iyi görünüyor ama yaklaşan disk küçüldüğü için kaçış sönüyor.
    arc_deg: float = 144.0
    radius_mm: float = 2.5        # ekran ekseninden ekrana uzaklık = sineğin başlangıç mesafesi
    follow: bool = False          # True: eski davranış, ekran sineğin başını izler
    follow_ms: float = 500.0      # izleme gecikmesinin zaman sabiti (VARSAYIM)
    texture_width: int = 540      # piksel; yükseklik orandan
    seated: bool = True           # post zemin hizasından başlasın (gezinme çubuğu yuvada)

    @property
    def width_mm(self) -> float:
        return np.radians(self.arc_deg) * self.radius_mm

    @property
    def height_mm(self) -> float:
        return self.width_mm * PHONE_ASPECT

    @property
    def texture_shape(self) -> tuple[int, int]:
        return int(round(self.texture_width * PHONE_ASPECT)), self.texture_width

    @property
    def base_z_mm(self) -> float:
        """Ekranın alt kenarının yüksekliği (yuvada negatif)."""
        if not self.seated:
            return 0.0
        h = self.texture_shape[0]
        return -(h - post_box(self.texture_shape)[1]) / h * self.height_mm


def _find(items, name):
    for x in items:
        if x.name == name:
            return x
    raise KeyError(name)


def _screen_mesh(cfg: SceneConfig, radius_mm: float, inward: bool) -> dict[str, list[float] | list[int]]:
    """Silindir parçası; u soldan sağa, v yukarıdan aşağı (sinekten bakınca).

    MuJoCo yüzlerin yalnızca ön tarafını çizer: ekranın yüzü içe (başa), arkası dışa bakar.
    """
    half = np.radians(cfg.arc_deg) / 2
    a = np.linspace(half, -half, _ARC_SEGMENTS + 1)  # sineğin solundan (+y) sağına
    u = np.linspace(0.0, 1.0, _ARC_SEGMENTS + 1)
    verts, uv, faces = [], [], []
    for z, v in ((0.0, 1.0), (cfg.height_mm, 0.0)):
        for ai, ui in zip(a, u):
            verts += [radius_mm * np.cos(ai), radius_mm * np.sin(ai), z]
            uv += [ui, v]
    n = _ARC_SEGMENTS + 1
    for i in range(_ARC_SEGMENTS):
        b0, b1, t0, t1 = i, i + 1, n + i, n + i + 1
        faces += [b0, b1, t1, b0, t1, t0] if inward else [b0, t1, b1, b0, t0, t1]
    return {"uservert": verts, "usertexcoord": uv, "userface": faces}


def add_to_world(spec: mj.MjSpec, cfg: SceneConfig) -> None:
    """Dünyanın MjSpec'ine gri arenayı ve ekranı ekler (derlemeden önce)."""
    sky = _find(spec.textures, "skybox")
    sky.rgb1 = sky.rgb2 = [SKY_GRAY] * 3
    checker = _find(spec.textures, "checker")
    checker.rgb1, checker.rgb2 = [FLOOR_GRAYS[0]] * 3, [FLOOR_GRAYS[1]] * 3
    _find(spec.materials, "grid").reflectance = 0.0
    spec.visual.headlight.ambient = [HEADLIGHT[0]] * 3
    spec.visual.headlight.diffuse = [HEADLIGHT[1]] * 3
    spec.visual.headlight.specular = [0.0] * 3
    spec.worldbody.add_light(name="tavan", type=mj.mjtLightType.mjLIGHT_DIRECTIONAL, pos=[0, 0, 50],
                             dir=[0, 0, -1], diffuse=[TOP_LIGHT] * 3, specular=[0.0] * 3,
                             castshadow=False)

    h, w = cfg.texture_shape
    tex = spec.add_texture(name=SCREEN_TEXTURE, type=mj.mjtTexture.mjTEXTURE_2D,
                           width=w, height=h, nchannel=3)
    tex.data = bytes(h * w * 3)  # kapalı ekran
    mat = spec.add_material(name=SCREEN_TEXTURE, emission=1.0, specular=0.0, shininess=0.0,
                            reflectance=0.0, rgba=[1, 1, 1, 1])
    mat.textures[int(mj.mjtTextureRole.mjTEXROLE_RGB)] = SCREEN_TEXTURE
    shell = mj.mjtMeshInertia.mjMESH_INERTIA_SHELL
    spec.add_mesh(name=SCREEN_BODY, inertia=shell, **_screen_mesh(cfg, cfg.radius_mm, inward=True))
    spec.add_mesh(name=f"{SCREEN_BODY}_arka", inertia=shell,
                  **_screen_mesh(cfg, cfg.radius_mm * 1.02, inward=False))
    body = spec.worldbody.add_body(name=SCREEN_BODY, mocap=True)
    body.add_geom(type=mj.mjtGeom.mjGEOM_MESH, meshname=SCREEN_BODY, material=SCREEN_TEXTURE,
                  contype=0, conaffinity=0, group=0)
    body.add_geom(type=mj.mjtGeom.mjGEOM_MESH, meshname=f"{SCREEN_BODY}_arka",
                  rgba=[BACK_GRAY, BACK_GRAY, BACK_GRAY, 1], contype=0, conaffinity=0, group=0)


def pixel_directions(cfg: SceneConfig, rows: np.ndarray, cols: np.ndarray,
                     distance_mm: float | None = None) -> np.ndarray:
    """Ekran dokusundaki piksellerin gözden bakış yönleri.

    Çerçeve ekranınki: x ileri (ekranın ortası), y sol, z yukarı. Dönüş (..., 3) birim vektör.

    Ekran artık dünyada sabit olduğu için mesafe sineğin nerede durduğuna bağlı (`Scene.
    distance_mm`); verilmezse sineğin eksende durduğu, yani `radius_mm` varsayılır.
    """
    h, w = cfg.texture_shape
    mesafe = cfg.radius_mm if distance_mm is None else float(distance_mm)
    rows, cols = np.broadcast_arrays(np.asarray(rows, dtype=float), np.asarray(cols, dtype=float))
    az = (0.5 - (cols + 0.5) / w) * np.radians(cfg.arc_deg)
    z = cfg.base_z_mm + (1.0 - (rows + 0.5) / h) * cfg.height_mm
    el = np.arctan2(z - EYE_HEIGHT_MM, mesafe)
    return np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], axis=-1)


class Scene:
    """Derlenmiş modeldeki ekran: görüntüsü ve sineği izlemesi."""

    def __init__(self, sim, fly_name: str, cfg: SceneConfig, head_body: str = "c_head",
                 thorax_body: str = "c_thorax"):
        self.sim = sim
        self.cfg = cfg
        m = sim.mj_model
        self._head = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{fly_name}/{head_body}")
        self._thorax = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{fly_name}/{thorax_body}")
        self._mocap = m.body_mocapid[mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, SCREEN_BODY)]
        self._tex = mj.mj_name2id(m, mj.mjtObj.mjOBJ_TEXTURE, SCREEN_TEXTURE)
        adr = m.tex_adr[self._tex]
        h, w = m.tex_height[self._tex], m.tex_width[self._tex]
        self._pixels = m.tex_data[adr:adr + h * w * 3].reshape(h, w, 3)
        self._renderers: list[mj.Renderer] = []
        self._pos = np.zeros(2)
        self._yaw = 0.0
        self._placed = False  # sabit ekran bir kez yerleşir
        self.image: np.ndarray = self._pixels.copy()

    @property
    def texture_shape(self) -> tuple[int, int]:
        """Ekran dokusunun piksel boyutu (yükseklik, genişlik)."""
        return self._pixels.shape[:2]

    def register(self, renderer: mj.Renderer) -> None:
        """Bu sahneyi çizen bir çizici; ekran görüntüsü değişince ona yeniden yüklenir."""
        self._renderers.append(renderer)

    def show(self, rgb: np.ndarray) -> None:
        """Ekranın yeni görüntüsü: (yükseklik, genişlik, 3), uint8 ya da [0, 1]."""
        rgb = np.asarray(rgb)
        if rgb.dtype != np.uint8:
            rgb = np.clip(np.round(rgb * 255), 0, 255).astype(np.uint8)
        if rgb.shape != self._pixels.shape:
            raise ValueError(f"ekran görüntüsü {self._pixels.shape} olmalı, {rgb.shape} verildi")
        # MuJoCo dokunun ilk satırını v = 0'a koyar; ağdaki v = 0 ekranın üst kenarı.
        self._pixels[:] = rgb
        self.image = rgb.copy()
        for r in self._renderers:
            r._gl_context.make_current()
            mj.mjr_uploadTexture(self.sim.mj_model, r._mjr_context, self._tex)

    def _target(self) -> tuple[np.ndarray, float]:
        d = self.sim.mj_data
        R = d.xmat[self._thorax].reshape(3, 3)
        return d.xpos[self._head][:2].copy(), float(np.arctan2(R[1, 0], R[0, 0]))

    def _apply(self) -> None:
        d = self.sim.mj_data
        d.mocap_pos[self._mocap] = [self._pos[0], self._pos[1], self.cfg.base_z_mm]
        d.mocap_quat[self._mocap] = [np.cos(self._yaw / 2), 0.0, 0.0, np.sin(self._yaw / 2)]

    def snap(self, force: bool = False) -> None:
        """Ekranı gecikmesiz sineğin önüne yerleştirir.

        Sabit ekranda (varsayılan) bu yalnızca **bir kez** olur: sonraki çağrılar ekranı yerinde
        bırakır. Yoksa deneyci sineği her doğrulttuğunda ekran da onunla taşınırdı ve ekran
        "sabit" olmazdı — `Body.place` sineği düştüğü yerde doğrultuyor (K-038).
        """
        m, d = self.sim.mj_model, self.sim.mj_data
        mj.mj_kinematics(m, d)  # fizik adımından sonra konumlar bir adım geriden gelir
        if force or self.cfg.follow or not self._placed:
            self._pos, self._yaw = self._target()
            self._placed = True
        self._apply()
        mj.mj_kinematics(m, d)

    def follow(self, dt_ms: float) -> None:
        """Ekranı sineğe göre günceller. Sabit ekranda (varsayılan) hiçbir şey yapmaz."""
        if not self.cfg.follow:
            return  # ekran dünyada duruyor; mesafeyi sineğin kendi yürüyüşü belirliyor
        pos, yaw = self._target()
        k = 1.0 - np.exp(-dt_ms / self.cfg.follow_ms)
        self._pos += (pos - self._pos) * k
        self._yaw += float(np.angle(np.exp(1j * (yaw - self._yaw)))) * k
        self._apply()

    @property
    def distance_mm(self) -> float:
        """Sineğin başının ekran yüzeyine uzaklığı (mm). Eksende duruyorsa `radius_mm`."""
        d = self.sim.mj_data
        ileri = np.array([np.cos(self._yaw), np.sin(self._yaw)])
        return float(self.cfg.radius_mm - (d.xpos[self._head][:2] - self._pos) @ ileri)

    @property
    def pose(self) -> tuple[np.ndarray, float]:
        """Ekran ekseninin konumu (mm) ve yönü (rad)."""
        return self._pos.copy(), self._yaw
