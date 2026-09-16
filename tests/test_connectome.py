import numpy as np
import pytest

from flybrain.anatomy import MOTOR, SENSORY, pools
from flybrain.connectome.build import ANNOTATIONS, TRANSMITTERS, WEIGHTS
from flybrain.connectome.connectome import load_connectome

pytestmark = pytest.mark.skipif(
    not all(p.exists() for p in (ANNOTATIONS, TRANSMITTERS, WEIGHTS)),
    reason="ham veri yok; önce python -m flybrain.connectome.download",
)


@pytest.fixture(scope="module")
def conn():
    return load_connectome()


def test_sizes(conn):
    assert conn.n == 165_122
    assert conn.W.shape == (conn.n, conn.n)
    assert 6_000_000 < conn.W.nnz < 6_500_000
    assert conn.neurons.bodyId.is_monotonic_increasing


def test_no_autapses(conn):
    assert conn.W.diagonal().sum() == 0


def test_signs_follow_presynaptic_transmitter(conn):
    W = conn.W
    col_sign = np.sign(W.data)
    pre = np.repeat(np.arange(conn.n), np.diff(W.indptr))
    assert (col_sign == conn.neurons.sign.to_numpy()[pre]).all()


def test_photoreceptors_are_inhibitory(conn):
    idx = pools(conn, SENSORY)["R1_R6"]
    assert (conn.neurons.sign.to_numpy()[idx] == -1).all()


@pytest.mark.parametrize("table", [SENSORY, MOTOR])
def test_pools_not_empty(conn, table):
    for name, idx in pools(conn, table).items():
        assert len(idx) > 0, name


def test_index_of_roundtrip(conn):
    idx = np.array([0, 10, conn.n - 1])
    assert (conn.index_of(conn.neurons.bodyId.to_numpy()[idx]) == idx).all()
    with pytest.raises(KeyError):
        conn.index_of([-1])
