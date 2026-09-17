"""Sinir kordonu hız modeli (K-025): model, boyutlar, ağ seçimi, ritim."""

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from flybrain.connectome.sizes import with_fallback
from flybrain.paths import RAW
from flybrain.sim.rate import RateNetwork, size_factors

T1_TABLE = RAW / "pugliese" / "wTable_20260210_vncRoisOnly.csv"


def test_rate_neuron_follows_its_equation():
    # Tek nöron, girdi I: kararlı durum R = Rmax·tanh(a/Rmax·(I − θ)).
    net = RateNetwork(sp.csr_matrix((1, 1)), np.array([1.0]), seed=0)
    net.run(500, current=np.array([50.0]))
    expected = net.r_max[0] * np.tanh(net.gain[0] / net.r_max[0] * (50.0 - net.threshold[0]))
    assert net.R[0] == pytest.approx(expected, rel=1e-3)
    net.reset()
    net.run(500, current=np.array([net.threshold[0] - 1.0]))
    assert net.R[0] == 0.0


def test_size_makes_neurons_less_excitable():
    net = RateNetwork(sp.csr_matrix((2, 2)), np.array([1.0, 4.0]), seed=0, size_reference=1.0)
    net.run(500, current=np.array([60.0, 60.0]))
    assert net.R[0] > net.R[1]
    assert size_factors(np.array([2.0, np.nan, 0.0]), reference=2.0).tolist() == [1.0, 1.0, 1.0]


def test_clamped_node_drives_but_does_not_integrate():
    W = sp.csr_matrix(np.array([[0.0, 1000.0], [1000.0, 0.0]]))  # 1 ← 0 ve 0 ← 1
    net = RateNetwork(W, np.ones(2), seed=0, clamped=np.array([1]))
    net.run(200, clamp_idx=np.array([1]), clamp_hz=np.array([20.0]))
    assert net.R[1] == 20.0 and net.R[0] > 0


def test_size_fallback_uses_type_median():
    df = pd.DataFrame({"size": [10.0, 30.0, np.nan, np.nan], "type": ["A", "A", "A", "B"],
                       "superclass": ["x", "x", "x", "x"]})
    size, source = with_fallback(df)
    assert size.tolist() == [10.0, 30.0, 20.0, 20.0]
    assert source.tolist() == ["olcum", "olcum", "tip_medyani", "sinif_medyani"]


@pytest.mark.skipif(not T1_TABLE.exists(), reason="Pugliese ve ark. ön bacak tablosu indirilmemiş")
def test_motor_network_contains_reference_front_leg_network():
    from flybrain.connectome import motor_network
    from flybrain.connectome.connectome import load_connectome

    conn = load_connectome()
    ours = set(motor_network.load(conn).bodyId)
    t1 = pd.read_csv(T1_TABLE, index_col=0)
    nn = conn.neurons.set_index("bodyId")
    ref = set(t1.bodyId[t1.bodyId.isin(nn.index)])
    assert len(ref - ours) / len(ref) < 0.01


@pytest.mark.skipif(not T1_TABLE.exists(), reason="Pugliese ve ark. ön bacak tablosu indirilmemiş")
def test_front_leg_rhythm_is_reproduced():
    from flybrain.experiments.vnc_rhythm import simulate

    runs = [simulate(seed) for seed in (0, 1)]
    for r in runs:
        assert r["skor"] >= 0.5
        assert 7.0 <= r["frekans_hz"] <= 15.0
