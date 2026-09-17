"""Sineğin kendi gözleriyle görme (body/sight.py)."""

import numpy as np
import pytest

from flybrain.fly import VISION


@pytest.fixture(scope="module")
def eyes():
    from flybrain.body.body import Body
    from flybrain.body.sight import FlyEyes
    from flybrain.connectome.connectome import load_connectome
    from flybrain.senses.eye import Eye

    conn = load_connectome()
    body = Body()
    body.step(np.zeros(len(body.dofs)), 2000)  # yere otur
    e = FlyEyes(body.sim, body.fly.name, "c_head", conn, VISION, Eye(conn))
    e.eye_model = Eye(conn)
    yield e
    e.close()
    body.close()


def test_columns_look_where_they_should(eyes):
    # Gökyüzü (varsayılan sahne) zeminden parlak: sırta bakan kolonlar karına bakanlardan parlak.
    frames = eyes.render()
    values = eyes.column_values(frames)
    name, idx, *_ = eyes.groups[0]
    _, _, _, theta = eyes.eye_model.neuron_directions(idx)
    lum = values[name]["lum"]
    up, down = lum[theta > 30], lum[theta < -30]
    assert np.nanmean(up) > np.nanmean(down) + 0.3
    assert np.isfinite(lum).mean() > 0.9


def test_static_scene_fades(eyes):
    eyes.reset()
    frames = eyes.render()
    eyes.encode(10.0, frames)
    # Sahne birden kararır: OFF yolu (L2) güçlü yanıt verir.
    dark = {s: f * 0.3 for s, f in frames.items()}
    first = eyes.encode(10.0, dark).hz.sum()
    assert eyes.last_contrast["L2"].min() < -0.5
    # Karanlık sürerse yanıt sönümlenir: geçici hücreler hemen, kalıcı hücreler uyumla.
    for _ in range(300):
        last = eyes.encode(10.0, dark).hz.sum()
    assert last < 0.2 * first
    assert all(np.abs(eyes.last_contrast[g[0]]).max() < 0.05 for g in eyes.groups if g[4] == "gecici")


def test_embodied_static_scene_does_not_trigger_escape():
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly

    f = EmbodiedFly(vision=EMBODIED_VISION)
    f.reset()
    gf = np.flatnonzero(f.conn.neurons.type.fillna("").to_numpy(dtype=object) == "DNp01")
    total = np.zeros(f.conn.n)
    orig = f.brain.run

    def run(d, s=None, **kw):
        r = orig(d, s, **kw)
        total[:] += r.counts
        return r

    f.brain.run = run
    f.run(300)
    assert total[gf].sum() == 0
    f.eyes.close()
    f.body.close()
