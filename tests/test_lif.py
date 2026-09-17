import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from flybrain.connectome.connectome import Connectome
from flybrain.sim import LIFParams, Simulator


def tiny(weights: dict[tuple[int, int], int], n: int) -> Connectome:
    """weights: (pre, post) -> işaretli sinaps sayısı."""
    pre, post, w = zip(*[(a, b, c) for (a, b), c in weights.items()]) if weights else ([], [], [])
    W = sp.csc_matrix((list(w), (list(post), list(pre))), shape=(n, n), dtype=np.int32)
    neurons = pd.DataFrame({"bodyId": np.arange(n), "type": ["x"] * n})
    return Connectome(neurons=neurons, W=W, label="tiny")


def test_silent_network_stays_silent():
    sim = Simulator(tiny({(0, 1): 100}, 2))
    res = sim.run(200)
    assert res.counts.sum() == 0
    assert np.allclose(sim.v, -52.0)


def test_poisson_drive_bounded_by_refractory():
    sim = Simulator(tiny({}, 1), seed=1)
    res = sim.run(1000, stim_idx=[0], stim_hz=10_000.0)
    # Her adımda girdi varken hız 1 / (22 adım × 0,1 ms) ≈ 454 Hz ile sınırlı.
    assert 400 < res.rates_hz[0] <= 1000 / 2.2 + 1


def test_moderate_poisson_rate_close_to_input():
    sim = Simulator(tiny({}, 1), seed=2)
    res = sim.run(20_000, stim_idx=[0], stim_hz=150.0)
    # Her Poisson olayı spike üretir; refrakter kayıp küçük.
    assert 120 < res.rates_hz[0] < 160


def test_synaptic_delay_is_exact():
    p = LIFParams()
    # 30 sinaps × 0,275 mV = 8,25 mV'lik g sıçraması: sonraki adımda eşiği aşmaz,
    # birkaç adımda aşar. Burada yalnızca g'nin tam gecikmede arttığını kontrol ediyoruz.
    sim = Simulator(tiny({(0, 1): 30}, 2), p)
    sim.v[0] = -40.0  # ilk adımda ateşler
    sim.run(p.dt_ms)  # adım 0: nöron 0 ateşler
    for _ in range(17):
        sim.run(p.dt_ms)
        assert sim.g[1] == 0.0
    sim.run(p.dt_ms)  # adım 18: iletim
    assert sim.g[1] == pytest.approx(30 * p.w_syn_mv)


def test_strong_excitation_propagates_and_inhibition_blocks():
    exc = Simulator(tiny({(0, 1): 200}, 2), seed=3)
    r = exc.run(500, stim_idx=[0], stim_hz=100.0)
    assert r.counts[1] > 0

    alone = Simulator(tiny({(0, 2): 200, (1, 2): 0}, 3), seed=3)
    inh = Simulator(tiny({(0, 2): 200, (1, 2): -400}, 3), seed=3)
    free = alone.run(1000, stim_idx=[0, 1], stim_hz=100.0).counts[2]
    blocked = inh.run(1000, stim_idx=[0, 1], stim_hz=100.0).counts[2]
    assert blocked < free / 3


def test_same_seed_same_result_and_state_persists():
    conn = tiny({(0, 1): 60, (1, 2): 60, (2, 0): 60}, 3)
    a, b = Simulator(conn, seed=7), Simulator(conn, seed=7)
    ra = a.run(300, stim_idx=[0], stim_hz=80.0)
    rb = b.run(300, stim_idx=[0], stim_hz=80.0)
    assert (ra.counts == rb.counts).all()
    assert a.step == 3000
    a.run(100)
    assert a.time_ms == pytest.approx(400)


def test_recording():
    sim = Simulator(tiny({}, 2), seed=4)
    res = sim.run(100, stim_idx=[0, 1], stim_hz=200.0, record=[1])
    assert (res.spike_neurons == 1).all()
    assert len(res.spike_steps) == res.counts[1]
    assert not res.record_overflow


@pytest.mark.parametrize("u", [0.0, 0.5])
def test_short_term_depression_scales_second_spike(u):
    p = LIFParams(std_u=u, std_tau_ms=100.0)
    sim = Simulator(tiny({(0, 1): 30}, 2), p)

    def force_spike_and_measure_delivery():
        sim.v[0] = -40.0
        sim.run(p.dt_ms)  # spike
        sim.run(17 * p.dt_ms)
        before = sim.g[1]
        sim.run(p.dt_ms)  # iletim
        return (sim.g[1] - before * sim._es) / (30 * p.w_syn_mv)

    first = force_spike_and_measure_delivery()
    sim.run(11 * p.dt_ms)  # ilk spike'tan 30 adım sonra ikinci spike
    second = force_spike_and_measure_delivery()
    assert first == pytest.approx(1.0)
    expected = 1.0 - u * np.exp(-30 * p.dt_ms / p.std_tau_ms)
    assert second == pytest.approx(expected)


def test_adaptation_limits_sustained_rate_but_not_kicks():
    base = Simulator(tiny({}, 1), seed=5).run(2000, stim_idx=[0], stim_hz=10_000.0)
    adapt = Simulator(tiny({}, 1), LIFParams(adapt_mv=2.0), seed=5).run(2000, stim_idx=[0], stim_hz=10_000.0)
    # Poisson darbesi (68,75 mV) adaptasyonu aşar: sürülen nöron yine refrakter sınırda ateşler.
    assert adapt.rates_hz[0] == pytest.approx(base.rates_hz[0], rel=0.05)

    # Sinaptik olarak sürülen nöron ise adaptasyonla yavaşlar.
    conn = tiny({(0, 1): 60}, 2)
    free = Simulator(conn, seed=6).run(2000, stim_idx=[0], stim_hz=300.0).counts[1]
    slowed = Simulator(conn, LIFParams(adapt_mv=2.0), seed=6).run(2000, stim_idx=[0], stim_hz=300.0).counts[1]
    assert slowed < 0.7 * free


def test_sensory_neurons_can_skip_depression():
    conn = tiny({(0, 1): 30}, 2)
    conn.neurons["superclass"] = ["cb_sensory", "cb_intrinsic"]
    p = LIFParams(std_u=0.5, std_skip_sensory=True)
    sim = Simulator(conn, p)
    assert sim._std_u.tolist() == [0.0, 0.5]


def test_tonic_bias_drives_firing_and_inhibition_modulates_it():
    # 10 mV'luk tonik akım eşiği (7 mV) aşar: nöron kendiliğinden ateşler.
    sim = Simulator(tiny({}, 1), bias_mv=np.array([10.0]))
    rate = sim.run(1000).rates_hz[0]
    assert rate > 5

    # Ketleyici girdi bu tonik ateşlemeyi azaltır.
    conn = tiny({(0, 1): -40}, 2)
    quiet = Simulator(conn, bias_mv=np.array([0.0, 10.0]), seed=1).run(1000).counts[1]
    inhibited = Simulator(conn, bias_mv=np.array([0.0, 10.0]), seed=1).run(
        1000, stim_idx=[0], stim_hz=100.0).counts[1]
    assert inhibited < 0.5 * quiet

    with pytest.raises(ValueError):
        Simulator(tiny({}, 2), bias_mv=np.zeros(3))


def test_std_exempt_neurons():
    sim = Simulator(tiny({}, 3), LIFParams(std_u=0.3), std_exempt=np.array([2]))
    assert sim._std_u.tolist() == [0.3, 0.3, 0.0]


def _random_network(n: int, seed: int) -> Connectome:
    rng = np.random.default_rng(seed)
    m = 20 * n
    pre, post = rng.integers(0, n, m), rng.integers(0, n, m)
    w = rng.integers(1, 30, m) * np.where(rng.random(m) < 0.25, -1, 1)
    W = sp.csc_matrix((w, (post, pre)), shape=(n, n), dtype=np.int32)
    neurons = pd.DataFrame({"bodyId": np.arange(n), "type": ["x"] * n})
    return Connectome(neurons=neurons, W=W, label="rastgele")


@pytest.mark.parametrize("params", [
    LIFParams(w_syn_mv=0.5, std_u=0.2, std_tau_ms=800.0),            # hızlı yol (a ve bias yok)
    LIFParams(w_syn_mv=0.5, std_u=0.2, std_tau_ms=800.0, adapt_mv=1.0),  # genel yol
])
def test_parallel_update_gives_same_result_for_any_thread_count(params):
    """Paralel güncelleme (Z-21): sonuç iş parçacığı sayısından bağımsız, bit düzeyinde aynı."""
    import numba

    conn = _random_network(3000, 0)
    drive = np.arange(0, 3000, 7)
    runs = []
    for threads in sorted({1, min(4, numba.config.NUMBA_NUM_THREADS)}):
        sim = Simulator(conn, params, seed=3)
        sim.threads = threads
        counts = sum(sim.run(1.0, stim_idx=drive, stim_hz=80.0, record=np.arange(50)).counts for _ in range(300))
        runs.append((counts, sim.v.copy(), sim.g.copy(), sim.x.copy()))
    assert runs[0][0].sum() > 0
    for a, b in zip(runs[0], runs[-1]):
        assert np.array_equal(a, b)


def test_bias_is_read_only_and_selects_update_path():
    sim = Simulator(tiny({}, 2))
    assert sim._lean
    with pytest.raises(ValueError):
        sim.bias_mv[0] = 1.0
    sim.bias_mv = np.array([0.0, 10.0])
    assert not sim._lean
    assert not Simulator(tiny({}, 2), LIFParams(adapt_mv=1.0))._lean
