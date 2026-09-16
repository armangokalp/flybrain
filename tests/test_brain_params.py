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


def test_post_reaches_descending_neurons_and_brain_settles(setup):
    from flybrain.experiments.post import VISION
    from flybrain.experiments.vision import natural_images
    from flybrain.senses.olfaction import OlfactoryEncoder
    from flybrain.senses.vision import VisionEncoder

    conn, _, _ = setup
    vis = VisionEncoder(conn, VISION)
    stim = vis.encode(natural_images(1, seed=11)["dogal_00"]) + OlfactoryEncoder(conn).encode("sabah kahvesi")
    sim = Simulator(conn, BRAIN_PARAMS, seed=1, std_exempt=vis.input_neurons)
    r = sim.run(500, stim)
    sim.run(300)
    after = sim.run(200)
    dn = conn.select(superclass="descending_neuron")
    assert (r.counts[dn] > 0).sum() > 5
    assert after.counts.sum() == 0
