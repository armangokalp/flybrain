import numpy as np
import pytest

from flybrain.connectome.build import WEIGHTS
from flybrain.motor.readout import CHANNELS
from flybrain.motor.selector import (
    BUDGET,
    MAX_WINDOWS,
    SAVE_MIN_GAP,
    ActionSelector,
    Calibration,
)

H = CHANNELS.index("hortum")
S = CHANNELS.index("sekme")


@pytest.fixture(scope="module")
def cal():
    rng = np.random.default_rng(0)
    rates = rng.gamma(2.0, 1.0, size=(2000, MAX_WINDOWS, len(CHANNELS)))
    rates[:, :, CHANNELS.index("geri")] = 0.0  # hiç değişmeyen kanal
    return Calibration.fit(rates, floor=np.full((MAX_WINDOWS, len(CHANNELS)), 0.01))


def test_fit_thresholds_follow_budget(cal):
    assert cal.disabled == ["geri"]
    for c in CHANNELS:
        if c not in cal.disabled:
            assert cal.realized[c] == pytest.approx(BUDGET[c], abs=0.01), c
    h_total = cal.realized["hortum"]
    assert cal.realized["kaydet"] <= 0.2 * h_total  # hortum kararlarının küçük bir kısmı kaydetme
    assert cal.save_theta >= cal.theta["hortum"] + SAVE_MIN_GAP
    assert cal.theta["yorum"] > cal.theta["ileri"]  # küçük bütçe → yüksek eşik
    assert set(cal.budget) == set(BUDGET)


def test_save_load_roundtrip(cal, tmp_path):
    path = tmp_path / "cal.json"
    cal.save(path)
    assert Calibration.load(path) == cal


def _rates_for_z(sel: ActionSelector, window: int, z: np.ndarray) -> np.ndarray:
    return sel.mean[window] + z * sel.std[window]


def test_keeps_looking_then_loses_interest(cal):
    sel = ActionSelector(cal)
    quiet = np.full(len(CHANNELS), -1.0)
    for w in range(MAX_WINDOWS - 1):
        assert sel.step(w, _rates_for_z(sel, w, quiet), 0.0) is None
    d = sel.step(MAX_WINDOWS - 1, _rates_for_z(sel, MAX_WINDOWS - 1, quiet), 0.0)
    assert d.action == "ilgi_kaybi" and d.dwell_ms == MAX_WINDOWS * 500


def test_like_and_save_intensity_levels(cal):
    sel = ActionSelector(cal)
    z = np.full(len(CHANNELS), -1.0)
    z[H] = (cal.theta["hortum"] + cal.save_theta) / 2  # orta şiddet
    assert sel.step(0, _rates_for_z(sel, 0, z), 0.0).action == "begen"
    z[H] = cal.save_theta + 0.1  # yüksek şiddet
    assert sel.step(0, _rates_for_z(sel, 0, z), 0.0).action == "kaydet"


def test_turn_direction_and_winner(cal):
    sel = ActionSelector(cal)
    z = np.full(len(CHANNELS), -1.0)
    z[S] = cal.theta["sekme"] + 2.0
    z[H] = cal.theta["hortum"] + 0.5
    assert sel.step(1, _rates_for_z(sel, 1, z), +1.0).action == "sekme_sol"
    assert sel.step(1, _rates_for_z(sel, 1, z), -1.0).action == "sekme_sag"


def test_single_spike_floor_limits_z():
    rates = np.zeros((100, MAX_WINDOWS, len(CHANNELS)))
    rates[:, 0, :] = np.random.default_rng(1).gamma(2.0, 1.0, size=(100, len(CHANNELS)))
    floor = np.full((MAX_WINDOWS, len(CHANNELS)), 0.5)
    cal = Calibration.fit(rates, floor)
    sel = ActionSelector(cal)
    one_spike = np.zeros(len(CHANNELS))
    one_spike[H] = 0.5  # sessiz pencerede tek spike
    assert sel.zscores(1, one_spike)[H] == pytest.approx(1.0)


def test_homeostasis_moves_thresholds_toward_budget(cal):
    from flybrain.motor.selector import Decision

    sel = ActionSelector(cal)
    before = sel.theta.copy()
    like = Decision("begen", "hortum", 0, 500, {}, "")
    for _ in range(20):
        sel.learn(like)
    after = sel.theta
    assert after[H] > before[H]                   # çok beğenildi → beğeni eşiği yükselir
    assert after[S] < before[S]                   # hiç sekme yok → sekme eşiği düşer
    assert sel.save_theta >= after[H] + SAVE_MIN_GAP
    # Kaydetmesiz beğeniler kaydetme eşiğini düşürür, kaydetmeler yükseltir.
    sel2 = ActionSelector(cal)
    start = sel2.save_theta
    sel2.learn(like)
    assert sel2.save_theta < start or sel2.save_theta == sel2.theta[H] + SAVE_MIN_GAP
    high = sel2.save_theta
    sel2.learn(Decision("kaydet", "hortum", 0, 500, {}, ""))
    assert sel2.save_theta > high
    frozen = ActionSelector(cal, homeostasis=False)
    frozen.learn(like)
    assert (frozen.theta == before).all()


def test_disabled_channel_never_wins(cal):
    sel = ActionSelector(cal)
    rates = _rates_for_z(sel, 0, np.full(len(CHANNELS), -1.0))
    rates[CHANNELS.index("geri")] = 1e6
    assert sel.step(0, rates, 0.0) is None


@pytest.mark.skipif(not WEIGHTS.exists(), reason="ham veri yok")
def test_readout_groups_are_anatomical():
    from flybrain.connectome.connectome import load_connectome
    from flybrain.motor.readout import MotorReadout

    conn = load_connectome()
    ro = MotorReadout(conn)
    sizes = ro.sizes()
    assert sizes["ileri"] == 381 and sizes["hortum"] == 67 and sizes["takip"] == 214
    assert sizes["yorum"] == 43 and sizes["cikis"] == 31
    counts = np.zeros(conn.n, dtype=np.int32)
    counts[ro.neck_left] = 2
    rates, turn = ro.rates(counts, 500)
    assert turn == 1.0 and rates[S] > 0 and rates[H] == 0
