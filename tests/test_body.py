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


def test_quiet_brain_keeps_body_still(conn):
    from flybrain.body.embodied import EmbodiedFly

    f = EmbodiedFly(conn, seed=0, proprioception=False)
    f.reset()
    before = f.body.dof_angles().copy()
    trace = f.run(300)
    a = trace.arrays()
    assert a["mn_spikes"].sum() == 0
    assert np.abs(f.body.dof_angles() - before).max() < 0.05
    f.body.close()


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


@pytest.fixture(scope="module")
def proprio(fly):
    return fly.proprio


def _group(proprio, name):
    g = next(g for g in proprio.groups if g.name == name)
    return g, np.isin(proprio.idx, g.neurons)


def test_proprio_assignments_match_published_signature():
    from flybrain.experiments.proprio import signature

    assert all(r["imzaya_uyuyor"] for r in signature())


def test_claw_rates_follow_tibia_angle(fly, proprio):
    j = fly.body.dofs.index("lm_trochanterfemur-lm_tibia-pitch")
    angles = fly.body.dof_angles().copy()
    still = np.zeros(len(fly.body.dofs))
    _, flex = _group(proprio, "lm:pence_bukulme:SNpp50")
    _, ext = _group(proprio, "lm:pence_acilma:SNpp51")
    angles[j] = 2.6  # iç açı ~31°: bükülmüş
    bent = proprio.rates(angles, still)
    angles[j] = 1.0  # iç açı ~123°: açılmış
    straight = proprio.rates(angles, still)
    assert bent[flex].sum() > 3 * straight[flex].sum()
    assert straight[ext].sum() > 3 * bent[ext].sum()


def test_hook_is_directional_and_club_is_not(fly, proprio):
    j = fly.body.dofs.index("lm_trochanterfemur-lm_tibia-pitch")
    angles = fly.body.dof_angles().copy()
    v = np.zeros(len(fly.body.dofs))
    _, hook_flex = _group(proprio, "lm:kanca_bukulme:SNpp41")
    _, club = _group(proprio, "lm:topuz:SNpp47")
    v[j] = 5.0
    flexing = proprio.rates(angles, v)
    v[j] = -5.0
    extending = proprio.rates(angles, v)
    assert flexing[hook_flex].sum() > 0 and extending[hook_flex].sum() == 0
    assert flexing[club].sum() == pytest.approx(extending[club].sum())
    assert proprio.rates(angles, np.zeros_like(v))[club].sum() == 0


def test_hair_plate_fires_near_its_limit(fly, proprio):
    g, sel = _group(proprio, "lm:kil_plakasi:SNpp45")
    k = fly.body.dofs.index(g.dof)
    lo, hi, _ = fly.body.dof_ranges()
    limit, other = (hi[k], lo[k]) if g.sign > 0 else (lo[k], hi[k])
    angles = fly.body.dof_angles().copy()
    still = np.zeros(len(angles))
    angles[k] = limit
    at_limit = proprio.rates(angles, still)[sel].sum()
    angles[k] = other
    far = proprio.rates(angles, still)[sel].sum()
    assert at_limit > 0.5 * 100.0 * len(g.neurons) and far < 1.0


def test_quiet_brain_with_proprioception_stays_calm(fly):
    fly.reset()
    z0 = fly.body.state().thorax_pos[2]
    trace = fly.run(500)
    a = trace.arrays()
    assert a["proprio_spikes"].sum() > 0
    # Az sayıda refleks spike'ı olabilir, ama beyin kaçak aktiviteye girmez ve sinek çökmez.
    assert a["mn_spikes"].sum() < 100
    assert a["thorax"][:, 2].min() > z0 - 0.15
