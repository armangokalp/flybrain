"""Gövde onayı (body/confirm.py, K-032) ve gövdeli sineğin karar döngüsü (body/viewer.py)."""

import numpy as np
import pytest

from flybrain.body.confirm import MEASURES, VISIBLE_DEG, VISIBLE_MM, BodyMeter, visible
from flybrain.motor.readout import CHANNELS
from flybrain.motor.selector import MAX_WINDOWS, ActionSelector, Calibration

C = {c: i for i, c in enumerate(CHANNELS)}


def _measures(**values) -> np.ndarray:
    m = np.zeros(len(MEASURES))
    for k, v in values.items():
        m[MEASURES.index(k)] = v
    return m


def test_small_movements_are_not_visible():
    below = np.radians(VISIBLE_DEG) * 0.9
    v = visible(_measures(bacak=below, hortum=below, bas=below, gogus_yukselme_mm=VISIBLE_MM * 0.9))
    assert not v.any()


def test_region_movement_confirms_its_channel():
    above = np.radians(VISIBLE_DEG) * 1.1
    v = visible(_measures(hortum=above, kanat=above))
    assert v[C["hortum"]] and v[C["yorum"]]
    assert not v[C["ileri"]] and not v[C["sekme"]] and not v[C["cikis"]]
    assert visible(_measures(gogus_ileri_mm=-2 * VISIBLE_MM))[C["geri"]]
    assert not visible(_measures(gogus_ileri_mm=2 * VISIBLE_MM))[C["geri"]]


def test_jump_confirms_only_escape():
    above = np.radians(VISIBLE_DEG) * 5
    v = visible(_measures(bacak=above, bas=above, karin=above, gogus_yukselme_mm=1.0))
    assert v[C["cikis"]] and v.sum() == 1


def test_body_meter_measures_path_and_heading():
    dofs = ["lf_coxa-lf_trochanterfemur-pitch", "c_head-c_rostrum-pitch", "c_thorax-c_head-yaw"]
    meter = BodyMeter(dofs)
    angles = np.zeros((3, 3))
    angles[:, 0] = [0.0, 0.1, 0.0]  # bacak: 0,2 rad yol
    yaw = np.pi / 2  # sinek +y yönüne bakıyor
    quat = np.array([np.cos(yaw / 2), 0.0, 0.0, np.sin(yaw / 2)])
    thorax = np.array([[0.0, 0.0, 0.6], [0.0, 0.2, 0.7], [0.0, 0.5, 0.6]])
    m = meter.measure({"angles": angles, "thorax": thorax, "thorax_quat": np.tile(quat, (3, 1))})
    assert m[MEASURES.index("bacak")] == pytest.approx(0.2)
    assert m[MEASURES.index("hortum")] == 0.0
    assert m[MEASURES.index("gogus_ileri_mm")] == pytest.approx(0.5)
    assert m[MEASURES.index("gogus_yukselme_mm")] == pytest.approx(0.1)


def test_fit_with_confirmation_never_picks_invisible_channel():
    rng = np.random.default_rng(0)
    rates = rng.gamma(2.0, 1.0, size=(1500, MAX_WINDOWS, len(CHANNELS)))
    vis = np.ones_like(rates, dtype=bool)
    vis[..., C["sekme"]] = False
    cal = Calibration.fit(rates, np.full((MAX_WINDOWS, len(CHANNELS)), 0.01), vis)
    assert cal.body_confirmation
    assert cal.realized["sekme"] == 0.0
    sel = ActionSelector(cal)
    x = np.array(cal.mean[0]) + 50 * np.array(cal.std[0])
    only_sekme = np.zeros(len(CHANNELS), dtype=bool)
    only_sekme[C["sekme"]] = True
    assert sel.step(0, x, 1.0, ~only_sekme).channel != "sekme"
    assert sel.step(0, x, 1.0, only_sekme).channel == "sekme"


def test_viewer_decisions_are_confirmed_by_body():
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.scene import SceneConfig
    from flybrain.body.viewer import FeedViewer
    from flybrain.experiments.calibrate import TEST_SEED, make_post
    from flybrain.motor.selector import CALIBRATION_EMBODIED_PATH

    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=SceneConfig(), seed=7)
    viewer = FeedViewer(fly, Calibration.load(CALIBRATION_EMBODIED_PATH), homeostasis=False)
    fly.reset()
    try:
        for k in range(3):
            d = viewer.look(make_post(k, TEST_SEED))
            assert d.body is not None and d.dwell_ms <= MAX_WINDOWS * 500
            if d.channel is not None:
                m = np.array([d.body[name] for name in MEASURES])
                assert visible(m)[C[d.channel]], d
    finally:
        fly.eyes.close()
        fly.body.close()
