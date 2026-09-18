"""Bağ: sinek ekrana kilitli (body/tether.py, K-040)."""

import numpy as np
import pytest

from flybrain.body.confirm import ESCAPE_DEG, MEASURES, VISIBLE_MM, visible
from flybrain.motor.readout import CHANNELS

C = {c: i for i, c in enumerate(CHANNELS)}


def _measures(**values) -> np.ndarray:
    m = np.zeros(len(MEASURES))
    for k, v in values.items():
        m[MEASURES.index(k)] = v
    return m


def test_tethered_escape_is_confirmed_by_jump_motion_not_by_thorax():
    """Bağlı sinek yükselemez; kaçışı sıçrama hareketi (TTM eklemi) onaylar."""
    firlayan = _measures(ttm=np.radians(2 * ESCAPE_DEG))
    assert visible(firlayan, tethered=True)[C["cikis"]]
    assert not visible(firlayan, tethered=False)[C["cikis"]]

    sicrayan = _measures(gogus_yukselme_mm=2 * VISIBLE_MM)
    assert visible(sicrayan, tethered=False)[C["cikis"]]
    assert not visible(sicrayan, tethered=True)[C["cikis"]]


def test_jump_motion_confirms_only_escape():
    """Sıçrama hareketi bütün gövdeyi savurur; sıçramadaki dışlama kuralı burada da geçerli."""
    yol = np.radians(5.0)
    v = visible(_measures(bacak=yol, bas=yol, karin=yol, ttm=np.radians(2 * ESCAPE_DEG)),
                tethered=True)
    assert v[C["cikis"]] and v.sum() == 1


def test_ordinary_leg_movement_is_not_an_escape():
    """TTM eklemi sinek dinlenirken de oynuyor; kaçış eşiği o gürültünün üstünde."""
    v = visible(_measures(ttm=np.radians(ESCAPE_DEG * 0.9)), tethered=True)
    assert not v[C["cikis"]]


def test_body_meter_measures_peak_excursion():
    from flybrain.body.confirm import BodyMeter

    meter = BodyMeter(["lf_coxa-lf_trochanterfemur-pitch"])
    quat = np.array([1.0, 0.0, 0.0, 0.0])
    # Göğüs önce 0,3 mm savrulup başladığı yere dönüyor: savrulma 0,3, yer değiştirme 0.
    thorax = np.array([[0.0, 0.0, 0.6], [0.3, 0.0, 0.6], [0.0, 0.0, 0.6]])
    m = meter.measure({"angles": np.zeros((3, 1)), "thorax": thorax,
                       "thorax_quat": np.tile(quat, (3, 1))})
    assert m[MEASURES.index("gogus_savrulma_mm")] == pytest.approx(0.3)
    assert m[MEASURES.index("gogus_mm")] == pytest.approx(0.0)


def test_tether_holds_the_thorax_where_it_was_attached():
    from flybrain.body.body import Body
    from flybrain.body.tether import TetherConfig

    body = Body(scene=None, tether=TetherConfig())
    try:
        assert not body.tether.attached  # bağ oturmadan önce takılı değil
        body.step(np.zeros(len(body.dofs)), 5000)  # sinek pasif duruşuna otursun
        body.tether.attach()
        assert body.tether.attached
        yer = body.state().thorax_pos.copy()
        body.step(np.zeros(len(body.dofs)), 20000)
        assert np.linalg.norm(body.state().thorax_pos - yer) < VISIBLE_MM
        assert body.tether.strain_mm < VISIBLE_MM
    finally:
        body.close()


def test_reset_releases_the_tether():
    from flybrain.body.body import Body
    from flybrain.body.tether import TetherConfig

    body = Body(scene=None, tether=TetherConfig())
    try:
        body.step(np.zeros(len(body.dofs)), 2000)
        body.tether.attach()
        body.reset()
        assert not body.tether.attached
    finally:
        body.close()


def test_struggle_does_not_end_the_post():
    """Bağlı sinekte 'çıkış' kararı postu bitirmez: yeni bir bakış nöbeti başlar (K-040)."""
    from flybrain.body.viewer import MAX_BOUTS, FeedViewer
    from flybrain.motor.selector import MAX_WINDOWS, Decision

    kararlar = [Decision("cikis", "cikis", 0, 500, {}, "test"),
                Decision("cikis", "cikis", 0, 500, {}, "test"),
                Decision("begen", "hortum", 1, 1000, {}, "test")]

    class SahteSecici:
        homeostasis = False

        def __init__(self):
            self.adim = 0

        def step(self, w, rates, turn, vis):
            d = kararlar[self.adim] if self.adim < len(kararlar) else None
            self.adim += 1
            return d

        def learn(self, d):
            pass

    viewer = object.__new__(FeedViewer)
    viewer.selector = SahteSecici()
    viewer.tethered = True
    viewer.counts = np.zeros(3, dtype=np.int64)
    viewer.posts = 0
    olcu = np.zeros(len(MEASURES))
    viewer._window = lambda stim, w: (np.zeros(len(CHANNELS)), 1.0, olcu, 1.0, 0)
    viewer._begin = lambda post: None

    class SahteSinek:
        recorder = None
        tether = object()

    viewer.fly = SahteSinek()
    cirpinmalar = []
    karar = viewer.look(None, on_struggle=lambda d, b: cirpinmalar.append(b))
    assert [d.action for d in kararlar[:2]] == ["cikis", "cikis"]
    assert cirpinmalar == [0, 1]       # iki kez kaçmaya çalıştı, ikisinde de kalamadı
    assert karar.action == "begen"     # sonra kendi iradesiyle başka bir karar verdi
    assert karar.bout == 2
    assert MAX_BOUTS >= 3 and MAX_WINDOWS >= 1


def test_struggle_loop_ends_with_loss_of_interest():
    """Sinek nöbet sınırına kadar hep kaçmaya çalışırsa post ilgi kaybıyla kapanır."""
    from flybrain.body.viewer import MAX_BOUTS, FeedViewer
    from flybrain.motor.selector import Decision

    class HepKacan:
        homeostasis = False

        def step(self, w, rates, turn, vis):
            return Decision("cikis", "cikis", 0, 500, {}, "test")

        def learn(self, d):
            pass

    viewer = object.__new__(FeedViewer)
    viewer.selector = HepKacan()
    viewer.tethered = True
    viewer.counts = np.zeros(3, dtype=np.int64)
    viewer.posts = 0
    viewer._window = lambda stim, w: (np.zeros(len(CHANNELS)), 1.0, np.zeros(len(MEASURES)), 1.0, 0)
    viewer._begin = lambda post: None

    class SahteSinek:
        recorder = None
        tether = object()

    viewer.fly = SahteSinek()
    sayac = []
    karar = viewer.look(None, on_struggle=lambda d, b: sayac.append(b))
    assert len(sayac) == MAX_BOUTS
    assert karar.action == "ilgi_kaybi" and "kaçış döngüsü" in karar.reason
