"""K-011 ayarının tam beyinde kararlı ve seçici kaldığını doğrular (yaklaşık 10 sn)."""

import numpy as np
import pytest

from flybrain.anatomy import MOTOR, SENSORY, pools
from flybrain.connectome.build import WEIGHTS
from flybrain.connectome.connectome import load_connectome
from flybrain.sim import BRAIN_PARAMS, Simulator

pytestmark = pytest.mark.skipif(not WEIGHTS.exists(), reason="ham veri yok")


@pytest.fixture(scope="module")
def setup():
    conn = load_connectome()
    return conn, pools(conn, SENSORY), pools(conn, MOTOR)


def _taste_trials(conn, stim, mn9, seeds=(10, 11, 12)):
    mn9_spikes, persistent = 0, 0
    for seed in seeds:
        sim = Simulator(conn, BRAIN_PARAMS, seed=seed)
        r = sim.run(500, stim_idx=stim, stim_hz=150.0)
        sim.run(300)
        after = sim.run(200)
        mn9_spikes += int(r.counts[mn9].sum())
        persistent += int((after.counts > 0).sum())
    return mn9_spikes, persistent


def test_sugar_drives_mn9_and_brain_settles(setup):
    conn, S, M = setup
    spikes, persistent = _taste_trials(conn, S["seker"], M["hortum"])
    assert spikes > 0
    assert persistent == 0


def test_bitter_does_not_drive_mn9(setup):
    conn, S, M = setup
    spikes, persistent = _taste_trials(conn, S["aci"], M["hortum"])
    assert spikes == 0
    assert persistent == 0


def test_silent_brain_stays_silent(setup):
    conn, _, _ = setup
    r = Simulator(conn, BRAIN_PARAMS).run(200)
    assert r.counts.sum() == 0
    assert np.isfinite(r.counts).all()
