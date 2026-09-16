"""3D gövde: kas tablosu, geometri ve neden-sonuç testleri."""

import numpy as np
import pytest

from flybrain.body.muscles import load_geometry
from flybrain.connectome.electrical import equivalent_synapses, psp_peak_factor
from flybrain.sim import BRAIN_PARAMS, Stimulus


@pytest.fixture(scope="module")
def conn():
    from flybrain.connectome.connectome import load_connectome

    return load_connectome()


@pytest.fixture(scope="module")
def fly(conn):
    from flybrain.body.embodied import EmbodiedFly

    f = EmbodiedFly(conn, seed=0)
    yield f
    f.body.close()


def _stim(fly, types, hz):
    t = fly.conn.neurons["type"].fillna("").astype(str).to_numpy(dtype=object)
    return Stimulus.of(np.flatnonzero(np.isin(t, types)), hz)


def test_geometry_signs_consistent():
    g = load_geometry()
    legs = g["nmf"]["legs"]
    assert len(legs) == 6
    for v in legs.values():
        assert v["tibia_flexion_sign"] == g["tibia_flexion_sign_ms"]
        assert v["tarsus_depression_sign"] == v["tibia_flexion_sign"]
    # Karşıt kaslar ters yönde çeker.
    m = g["muscles"]
    assert m["Tibia_flex_93434"]["arm_mm_per_rad"]["tibia_pitch"] * m["Tibia_extensor_93932"]["arm_mm_per_rad"]["tibia_pitch"] < 0
    assert m["trochanter_flexor_a"]["arm_mm_per_rad"]["trochanter_pitch"] * m["trochanter_extensor"]["arm_mm_per_rad"]["trochanter_pitch"] < 0


def test_muscle_table_covers_motor_neurons(fly):
    table = fly.table
    names = {m.name for m in table.muscles}
    for leg in ("lf", "lm", "lh", "rf", "rm", "rh"):
        assert f"{leg}:Tibia_flex_93434" in names
        assert f"{leg}:Tibia_extensor_93932" in names
    assert {"lm:TTM", "rm:TTM", "hortum:MN9"} <= names
    assert sum(len(m.mn) for m in table.muscles) >= 650


def test_electrical_weight_gives_one_to_one_transmission():
    p = BRAIN_PARAMS
    w = equivalent_synapses(p)
    peak = psp_peak_factor(p) * p.w_syn_mv * w
    assert peak >= 2 * (p.v_thresh_mv - p.v_rest_mv)


def test_quiet_brain_keeps_body_still(fly):
    fly.reset()
    before = fly.body.dof_angles().copy()
    trace = fly.run(300)
    a = trace.arrays()
    assert a["mn_spikes"].sum() == 0
    assert np.abs(fly.body.dof_angles() - before).max() < 0.05


def test_mn9_extends_proboscis(fly):
    fly.reset()
    j = fly.body.dofs.index("c_head-c_rostrum-pitch")
    before = fly.body.dof_angles()[j]
    fly.run(300, _stim(fly, ["MN9"], 150.0))
    sign = load_geometry()["nmf"]["rostrum_protraction"]["sign"]
    assert sign * (fly.body.dof_angles()[j] - before) > 0.3


def test_giant_fiber_triggers_jump(fly):
    fly.reset()
    z0 = fly.body.state().thorax_pos[2]
    trace = fly.run(15, _stim(fly, ["DNp01"], 300.0))
    trace = fly.run(150, trace=trace)
    a = trace.arrays()
    ttm = np.isin(fly.muscles.mn, np.flatnonzero(fly.conn.neurons["type"].fillna("").astype(str) == "TTMn"))
    assert a["mn_spikes"][:, ttm].sum() >= 2
    assert a["thorax"][:, 2].max() - z0 > 1.0
