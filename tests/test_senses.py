import numpy as np
import pytest

from flybrain.connectome.build import WEIGHTS
from flybrain.connectome.connectome import load_connectome
from flybrain.senses.eye import Eye, lattice_xy
from flybrain.senses.olfaction import GLOMERULI_PER_WORD, OlfactoryEncoder, tokenize
from flybrain.senses.reward import RewardEncoder
from flybrain.senses.vision import VisionConfig, VisionEncoder
from flybrain.sim.stimulus import MAX_HZ, Stimulus


def test_tokenize():
    assert tokenize("Merhaba DÜNYA! #kahve ☕️ İstanbul, 2026") == [
        "merhaba", "dünya", "kahve", "☕", "istanbul", "2026"
    ]
    assert tokenize("...!!!") == []


def test_stimulus_merge_and_cap():
    s = Stimulus.of([3, 1, 3], [100.0, 50.0, 350.0])
    assert s.idx.tolist() == [1, 3]
    assert s.hz.tolist() == [50.0, MAX_HZ]
    assert len(Stimulus.of([1], [0.0])) == 0
    assert len(Stimulus.empty() + s) == 2


def test_lattice_neighbors_equidistant():
    p = lattice_xy([10, 11, 10, 11], [10, 10, 11, 11])
    d = np.linalg.norm(p[1:] - p[0], axis=1)
    assert np.allclose(d, 1.0)


needs_data = pytest.mark.skipif(not WEIGHTS.exists(), reason="ham veri yok")


@pytest.fixture(scope="module")
def conn():
    return load_connectome()


@needs_data
def test_odor_is_deterministic_and_saturates(conn):
    enc = OlfactoryEncoder(conn)
    assert len(enc.glomeruli) == 53
    a = enc.odor("kahve")
    assert a == enc.odor("kahve") and len(a) == GLOMERULI_PER_WORD
    distinct = {enc.odor(w) for w in ["kahve", "çay", "deniz", "kedi", "sinek", "gece"]}
    assert len(distinct) >= 5

    one = enc.encode("kahve")
    assert np.allclose(one.hz, 150.0)
    assert set(conn.neurons.type.to_numpy()[one.idx]) == set(a)
    three = enc.encode("kahve kahve kahve")
    assert np.allclose(three.hz, 180.0)
    assert len(enc.encode("!!!")) == 0


@needs_data
def test_reward(conn):
    enc = RewardEncoder(conn)
    assert len(enc.encode(0, 0)) == 0
    s = enc.encode(rewards=5)
    assert len(s) == len(enc.pam) and np.allclose(s.hz, 75.0)


@needs_data
def test_eye_orientation(conn):
    eye = Eye(conn)
    assert eye.view.theta_r2 > 0.8
    # Üst kenar (dorsal rim) kolonları yukarıda, ızgaranın alt ucu aşağıda olmalı.
    _, dra_theta = eye.view([30.0], [34.7])
    _, low_theta = eye.view([5.0], [5.0])
    assert dra_theta[0] > 40 and low_theta[0] < -20


@needs_data
@pytest.mark.parametrize("mode", ["off", "onoff"])
def test_vision_contrast_modes(conn, mode):
    enc = VisionEncoder(conn, VisionConfig(mode=mode))
    assert len(enc.gray()) == 0
    img = np.full((100, 200, 3), 0.8)
    img[:, :100] = 0.1  # sol yarı karanlık
    s = enc.encode(img)
    off = np.isin(s.idx, enc.groups[0][1])
    sides = conn.neurons.side.to_numpy()[s.idx[off]]
    assert (sides == "L").mean() > 0.95


@needs_data
def test_vision_foto_mode(conn):
    enc = VisionEncoder(conn, VisionConfig(mode="foto"))
    gray = enc.gray()
    assert len(gray) > 3000 and np.allclose(gray.hz, 50.0)
    assert enc.bias_mv is not None and enc.bias_mv.max() == 9.0
    # Kırmızı, sinek için neredeyse karanlıktır.
    red = enc.encode(np.dstack([np.ones((50, 50)), np.zeros((50, 50)), np.zeros((50, 50))]))
    green = enc.encode(np.dstack([np.zeros((50, 50)), np.ones((50, 50)), np.zeros((50, 50))]))
    assert len(red) == len(green)  # tek renkli görselde kontrast yok: hepsi taban hızda
