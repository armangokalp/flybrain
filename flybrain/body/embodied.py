"""Beyin + kaslar + gövde: kapalı döngünün çekirdeği.

Her COUPLE_MS milisaniyede:
  1. Gövdenin eklem açıları ve hızları propriyoseptör hızlarına çevrilir.
  2. Sinir sistemi COUPLE_MS boyunca çalışır (propriyosepsiyon + dışarıdan verilen uyarım):
     varsayılan tamamen LIF; `vnc="rate"` ile bacak motor ağı hız modelinde (K-025, deneysel).
  3. Motor nöronların spike sayıları kas modeline gider.
  4. Kas torkları gövdeye uygulanır, fizik aynı süre boyunca ilerler.

Görme açıksa her VISION_EVERY_MS milisaniyede sineğin göz kameraları sahneyi çizer ve
göz kolonlarının uyarımı güncellenir (body/sight.py).

Yeniden yerleştirme (kullanıcı kararı, docs/09-govde.md 17): sinek REPOSITION_MS'den uzun
süre dik değilse (sıçramadan sonra sırtüstü ya da yan yatıp kaldığında, Z-26), deneyci onu
oturma sonundaki dik duruşuna geri koyar: olduğu yerde, telefona dönük. Deneyci sineği
HOLD_MS boyunca bu duruşta tutar, sonra bırakır. Tutma sırasında beyin, görme ve
propriyosepsiyon çalışır; gözler yeni görüntüye uyum sağlar, ama gövde hareket etmez.
Tutma olmadan görüntünün ani değişimi hemen yeni bir kaçış tetikliyordu. Bu bir dünya
müdahalesidir; her olay `repositions` ve Trace'e kaydedilir. Sahne kurulmuşsa varsayılan
olarak açıktır.

Sahne açıksa (body/scene.py) telefon ekranı her adımda sineği gecikmeyle izler. Ekrandaki
akış (body/phone.py) `show_post` ile doğrudan, `scroll_to_post` ile kaydırılarak,
`fade_to_post` ile solarak değişir; ekran görüntüsü görmeyle aynı aralıkla yenilenir.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from flybrain.body.body import TIMESTEP_S, Body
from flybrain.body.muscles import MuscleModel, build_table
from flybrain.body.phone import FADE_MS, SCROLL_MS, FeedPost, PhoneFeed, ScreenSource
from flybrain.body.proprio import build_proprioception
from flybrain.body.scene import SceneConfig
from flybrain.body.sight import FlyEyes
from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.connectome.electrical import with_electrical
from flybrain.sim import BRAIN_PARAMS, LIFParams, Simulator, Stimulus
from flybrain.senses.vision import VisionConfig
from flybrain.sim.hybrid import HybridCNS

COUPLE_MS = 1.0
# Nötr pozdan pasif duruşa oturma süresi (ölçüm: 500 ms'den sonra eklemler < 0,002 rad/100 ms).
SETTLE_MS = 500.0
# Oturma beyin çalışırken yapılıyor; rastgele arka plan etkinliği sineği ~40 oturmada bir
# yatık bırakıyor (diklik ~0,38). Bu durumda oturma yeniden yapılır (docs/09-govde.md 17.7).
SETTLE_TRIES = 5
# Oturmadan sonra görme açılmadan önce propriyosepsiyonun ısınma süresi. Propriyosepsiyonun
# açıldığı ilk 300 ms'de bacak motor nöronları sonrakinin ~2 katı ateşliyor (ölçüm: 14-21'e
# karşı 0-14 spike); bu geçici hareket görmeyle birleşince kaçışı tetikleyebiliyordu.
PROPRIO_WARMUP_MS = 300.0
# Gövdeli sinekte görme kazancı (K-029). Gövdesiz sineğin 250 Hz'i (K-012) durağan bir postun
# sürekli kontrastı için seçilmişti. Zamansal kodlamada sineğin dinlenirken kendi küçük
# hareketleri de görme uyarımı üretiyor ve 250 Hz'de telefon ekranına bakan sinek çoğu
# denemede bir saniye içinde kendiliğinden kaçıyordu. 125 Hz'de yaklaşan diske kaçış %91,
# durağan ekranda kendiliğinden dev lif ateşlemesi ~17 sn'de bir (docs/09-govde.md 12).
EMBODIED_VISION = VisionConfig(mode="onoff", r_max_hz=125.0)
# Yeniden yerleştirme (K-031): göğüs dikeyinin kosinüsü bunun altındaysa sinek "dik değil"
# sayılır (~25° yatma). Dik duran sinekte bu değer 0,98'in altına pek inmiyor; yan yatıp
# kalan sinekte 0,55–0,80 (docs/09-govde.md 17.7). İlk sürümde eşik 0,5'ti ve yatık sinek
# dakikalarca yerleştirilmiyordu.
UPRIGHT_MIN = 0.9
# Dik olmayan süre REPOSITION_MS'ye ulaşınca deneyci sineği yeniden yerleştirir (VARSAYIM).
# Sayaç dik anlarda sıfırlanmaz, RECOVER_RATE hızıyla azalır: sallanan sinek çizginin iki
# yanına geçip dursa da zamanla yerleştirilir.
REPOSITION_MS = 1000.0
RECOVER_RATE = 0.5
# Deneycinin sineği yerleştirdikten sonra tuttuğu süre (VARSAYIM; görme uyumunun zaman
# sabitiyle aynı, ADAPT_MS).
HOLD_MS = 1000.0
# Göz görüntüsünün yenilenme aralığı (VARSAYIM; 100 kare/sn, sineğin titreşim birleşme
# frekansının altında; çizim maliyeti nedeniyle).
VISION_EVERY_MS = 10.0


def down_time(down_ms: float, upright: float, dt_ms: float) -> float:
    """Dik olmayan süre sayacı: sinek dik değilken artar, dikken RECOVER_RATE hızıyla azalır."""
    if upright < UPRIGHT_MIN:
        return down_ms + dt_ms
    return max(0.0, down_ms - RECOVER_RATE * dt_ms)


@dataclass
class Trace:
    """Bir koşunun kaydı: zaman, gövde, kas uyarılmaları, videonun kareleri."""

    t_ms: list[float] = field(default_factory=list)
    thorax: list[np.ndarray] = field(default_factory=list)
    thorax_quat: list[np.ndarray] = field(default_factory=list)
    angles: list[np.ndarray] = field(default_factory=list)
    activation: list[np.ndarray] = field(default_factory=list)
    mn_spikes: list[np.ndarray] = field(default_factory=list)  # önceki kayıttan bu yana, muscles.mn sırası
    proprio_spikes: list[np.ndarray] = field(default_factory=list)  # önceki kayıttan bu yana, proprio.idx sırası
    vision_hz: list[float] = field(default_factory=list)  # kayıt anında görme uyarımının toplam hızı
    repositions: list[float] = field(default_factory=list)  # deneycinin sineği yeniden yerleştirdiği anlar (ms)
    frames: dict[str, list[np.ndarray]] = field(default_factory=dict)

    def arrays(self) -> dict[str, np.ndarray]:
        return {
            "t_ms": np.array(self.t_ms),
            "thorax": np.array(self.thorax),
            "thorax_quat": np.array(self.thorax_quat),
            "angles": np.array(self.angles),
            "activation": np.array(self.activation),
            "mn_spikes": np.array(self.mn_spikes),
            "proprio_spikes": np.array(self.proprio_spikes),
            "vision_hz": np.array(self.vision_hz),
        }


class EmbodiedFly:
    def __init__(
        self,
        conn: Connectome | None = None,
        seed: int = 0,
        params: LIFParams = BRAIN_PARAMS,
        std_exempt: np.ndarray | None = None,
        camera_res: tuple[int, int] = (360, 480),
        electrical: bool = True,
        proprioception: bool = True,
        vnc: str = "lif",
        vision: VisionConfig | None = None,
        scene: SceneConfig | None = None,
        reposition: bool | None = None,
    ):
        """vnc: "lif" — tüm sinir sistemi LIF; "rate" — bacak motor ağı hız modeliyle (K-025, deneysel).
        vision: verilirse sinek sahneyi kendi gözleriyle görür (body/sight.py).
        scene: verilirse gri arena ve sineği izleyen telefon ekranı (body/scene.py).
        reposition: düşen sineği deneyci yeniden yerleştirsin mi; None ise sahne varsa evet.
        """
        self.conn = conn or load_connectome()
        self.gap_junctions = []
        if electrical:
            self.conn, gap_exempt, self.gap_junctions = with_electrical(self.conn, params)
            std_exempt = gap_exempt if std_exempt is None else np.union1d(std_exempt, gap_exempt)
        self.body = Body(camera_res=camera_res, scene=scene)
        self.scene = self.body.scene
        self.feed: ScreenSource | None = PhoneFeed(scene.texture_shape) if scene is not None else None
        self.eyes = None
        if vision is not None:
            if vision.mode == "foto":
                raise ValueError("gövdeli sinekte 'foto' görme yöntemi henüz desteklenmiyor")
            self.eyes = FlyEyes(self.body.sim, self.body.fly.name, "c_head", self.conn, vision)
            if self.scene is not None:
                self.scene.register(self.eyes.renderer)
            std_exempt = self.eyes.input_neurons if std_exempt is None else np.union1d(std_exempt, self.eyes.input_neurons)
        self._vision_stim = Stimulus.empty()
        self.table = build_table(self.conn, self.body.passive)
        self.muscles = MuscleModel(self.table, self.body.dofs, self.body.dof_ranges())
        self.proprio = None
        if proprioception:
            flex = {leg: v["tibia_flexion_sign"] for leg, v in self.body.geom["nmf"]["legs"].items()}
            self.proprio = build_proprioception(self.conn, self.table, self.body.dofs,
                                                self.body.dof_ranges(), flex)
        self.vnc = vnc
        if vnc == "rate":
            sensors = self.proprio.idx if self.proprio is not None else None
            self.cns = HybridCNS(self.conn, params, seed=seed, std_exempt=std_exempt, sensors=sensors)
            self.brain = self.cns.brain
        elif vnc == "lif":
            self.cns = None
            self.brain = Simulator(self.conn, params, seed=seed, std_exempt=std_exempt)
        else:
            raise ValueError(f"bilinmeyen sinir kordonu modeli: {vnc}")
        self._steps = int(round(COUPLE_MS / 1000 / TIMESTEP_S))
        self.reposition = scene is not None if reposition is None else reposition
        self.repositions: list[float] = []
        self._standing: np.ndarray | None = None
        self._down_ms = 0.0
        self._hold: np.ndarray | None = None
        self._hold_ms = 0.0
        # Verilirse her adımda bütün nöronların spike sayıları buna eklenir (karar okuması için).
        self.spike_counter: np.ndarray | None = None
        # Verilirse her adımın sonunda çağrılır: canlı izleme (viz/live.py).
        self.on_step = None
        # Sonraki posta solarak geçişin süresi (K-030); gerçek feed'de uzatılabiliyor.
        self.fade_ms = FADE_MS
        # Verilirse her adımın sonunda (fizikten ve deneyci müdahalesinden sonra) çağrılır:
        # recorder.step(sinek, spike sayıları) (viz/record.py).
        self.recorder = None
        self._joint_index = {n: i for i, n in enumerate(self.body.joint_names)}

    def joint(self, name: str) -> int:
        return self._joint_index[name]

    def reset(self, settle: bool = True):
        """Beyni ve gövdeyi sıfırlar; gövde pasif duruşuna oturana kadar ikisi birlikte çalışır.

        Oturma sırasında propriyosepsiyon ve görme kapalıdır: model sineği havada nötr pozda
        başlatır ve zemine iniş gerçek bir durum değildir. Beyin bu sürede girdi almaz.
        Ardından PROPRIO_WARMUP_MS boyunca yalnızca propriyosepsiyon açıktır; görme en son açılır.
        Oturma sonunda sinek dik değilse (UPRIGHT_MIN) oturma baştan yapılır.
        """
        for _ in range(SETTLE_TRIES if settle else 1):
            self._clear()
            if not settle:
                return
            proprio, self.proprio = self.proprio, None
            eyes, self.eyes = self.eyes, None
            try:
                self.run(SETTLE_MS)
                if proprio is not None:
                    self.proprio = proprio
                    self.run(PROPRIO_WARMUP_MS)
            finally:
                self.proprio, self.eyes = proprio, eyes
            if self.body.upright() >= UPRIGHT_MIN:
                break
        else:
            raise RuntimeError(f"sinek {SETTLE_TRIES} denemede dik oturmadı")
        self._standing = self.body.snapshot()
        if self.scene is not None:
            self.scene.snap(force=True)  # oturmuş duruşa göre yerleşsin
        if self.eyes is not None:
            self.eyes.reset()

    def _clear(self) -> None:
        if self.cns is not None:
            self.cns.reset()
        else:
            self.brain.reset()
        self.body.reset()
        self.muscles.reset()
        self._vision_stim = Stimulus.empty()
        self._standing = None
        self._down_ms = 0.0
        self._hold = None
        self._hold_ms = 0.0
        self.repositions = []
        if self.eyes is not None:
            self.eyes.reset()

    def place_upright(self) -> None:
        """Deneyci sineği oturma sonundaki dik duruşuna koyar: olduğu yerde, telefona dönük."""
        if self._standing is None:
            raise RuntimeError("dik duruş yok: önce reset() ile oturtulmalı")
        yaw = self.scene.pose[1] if self.scene is not None else 0.0
        self.body.place(self._standing, yaw)
        if self.scene is not None:
            self.scene.snap()
        self._down_ms = 0.0
        self._hold = self.body.snapshot()
        self._hold_ms = HOLD_MS
        self.repositions.append(self.brain.time_ms)

    @property
    def held(self) -> bool:
        """Deneyci sineği şu anda tutuyor mu."""
        return self._hold_ms > 0

    def _need_feed(self) -> ScreenSource:
        if self.feed is None:
            raise RuntimeError("sahne yok: EmbodiedFly(scene=SceneConfig()) ile kurulmalı")
        return self.feed

    def show_post(self, post: FeedPost) -> None:
        """Ekrandaki akışta yeni posta kaydırmadan geçer (ekran hemen değişir)."""
        self._need_feed().show(post)
        self._refresh_screen()

    def next_post(self, post: FeedPost) -> None:
        """Akışta sonraki posta geçer: solarak (K-030). Geçiş sonraki `run` sırasında oynar."""
        self.fade_to_post(post, self.fade_ms)

    def scroll_to_post(self, post: FeedPost, duration_ms: float = SCROLL_MS) -> None:
        """Akışı yeni posta kaydırır; kaydırma sonraki `run` sırasında oynar."""
        self._need_feed().scroll_to(post, self.brain.time_ms, duration_ms)

    def fade_to_post(self, post: FeedPost, duration_ms: float = FADE_MS) -> None:
        """Ekran yeni posta solarak geçer; geçiş sonraki `run` sırasında oynar."""
        self._need_feed().fade_to(post, self.brain.time_ms, duration_ms)
        self._refresh_screen()

    def play_video(self, video) -> None:
        """Bakılan postun görselinde video oynatır (body/phone.py `PhoneFeed.play`)."""
        feed = self._need_feed()
        if not hasattr(feed, "play"):
            raise RuntimeError("bu ekran kaynağında video oynatma yok")
        feed.play(video, self.brain.time_ms)

    def _refresh_screen(self) -> None:
        if self.feed is not None and self.feed.update(self.brain.time_ms):
            self.scene.show(self.feed.frame())

    def run(
        self,
        duration_ms: float,
        stim: Stimulus | None = None,
        cameras: tuple[str, ...] = (),
        fps: float = 30.0,
        trace: Trace | None = None,
        record_every_ms: float = 5.0,
        on_step: Callable[["EmbodiedFly"], None] | None = None,
    ) -> Trace:
        """on_step: her eşleşme adımında fizikten önce çağrılır (deneylerde dış prob için)."""
        trace = trace or Trace()
        for c in cameras:
            trace.frames.setdefault(c, [])
        n = int(round(duration_ms / COUPLE_MS))
        frame_every = max(1, int(round(1000 / fps / COUPLE_MS)))
        rec_every = max(1, int(round(record_every_ms / COUPLE_MS)))
        mn = self.muscles.mn
        acc = np.zeros(len(mn), dtype=np.int32)
        pr = self.proprio.idx if self.proprio is not None else np.zeros(0, dtype=np.int64)
        pr_acc = np.zeros(len(pr), dtype=np.int32)
        vision_every = max(1, int(round(VISION_EVERY_MS / COUPLE_MS)))
        for k in range(n):
            if int(round(self.brain.time_ms / COUPLE_MS)) % vision_every == 0:
                self._refresh_screen()
                if self.eyes is not None:
                    self._vision_stim = self.eyes.encode(VISION_EVERY_MS)
            drive_stim = stim
            if len(self._vision_stim):
                drive_stim = self._vision_stim if stim is None or len(stim) == 0 else stim + self._vision_stim
            angles = self.body.dof_angles()
            hz = self.proprio.rates(angles, self.body.dof_velocities()) if self.proprio is not None else None
            if self.cns is not None:
                result = self.cns.step(COUPLE_MS, drive_stim, hz)
            else:
                drive = drive_stim
                if hz is not None:
                    drive = Stimulus(pr, hz) if drive is None or len(drive) == 0 else Stimulus.of(np.r_[pr, drive.idx], np.r_[hz, drive.hz])
                result = self.brain.run(COUPLE_MS, drive).counts
            if self.spike_counter is not None:
                self.spike_counter += result
            counts = result[mn]
            acc += counts
            pr_acc += result[pr]
            torques = self.muscles.step(counts, COUPLE_MS, angles)
            if on_step is not None:
                on_step(self)
            if self.scene is not None:
                self.scene.follow(COUPLE_MS)
            self.body.step(torques, self._steps)
            if self._hold_ms > 0:
                self.body.hold(self._hold)
                self._hold_ms -= COUPLE_MS
            elif self.reposition and self._standing is not None:
                self._down_ms = down_time(self._down_ms, self.body.upright(), COUPLE_MS)
                if self._down_ms >= REPOSITION_MS:
                    self.place_upright()
                    trace.repositions.append(self.brain.time_ms)
            if self.recorder is not None:
                self.recorder.step(self, result)
            if self.on_step is not None:
                self.on_step(self)
            if cameras and k % frame_every == 0:
                for c in cameras:
                    trace.frames[c].append(self.body.render(c))
            if k % rec_every == 0:
                s = self.body.state()
                trace.t_ms.append(self.brain.time_ms)
                trace.thorax.append(s.thorax_pos)
                trace.thorax_quat.append(s.thorax_quat)
                trace.angles.append(s.joint_angles)
                trace.activation.append(self.muscles.activation.copy())
                trace.mn_spikes.append(acc.copy())
                trace.proprio_spikes.append(pr_acc.copy())
                trace.vision_hz.append(float(self._vision_stim.hz.sum()))
                acc[:] = 0
                pr_acc[:] = 0
        return trace
