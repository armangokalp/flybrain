"""Telefon ekranlı sahne (body/scene.py) ve ekran görüntüsü (body/phone.py)."""

import numpy as np
import pytest

from flybrain.body.phone import SCROLL_MS, FeedPost, PhoneFeed, post_box
from flybrain.body.scene import PHONE_ASPECT, SceneConfig
from flybrain.fly import VISION

CFG = SceneConfig()


def _post(value: float) -> FeedPost:
    return FeedPost(np.full((50, 40, 3), value))


def test_phone_has_phone_proportions_and_post_sits_above_nav_bar():
    h, w = CFG.texture_shape
    assert h / w == pytest.approx(PHONE_ASPECT, rel=0.01)
    assert CFG.height_mm / CFG.width_mm == pytest.approx(PHONE_ASPECT)
    top, bottom, left, right = post_box((h, w))
    assert (bottom - top) / (right - left) == pytest.approx(5 / 4, rel=0.01)
    assert 0.85 < bottom / h < 0.95
    # Yuvaya oturan telefonda postun alt kenarı zemin hizasında.
    assert CFG.base_z_mm + (h - bottom) / h * CFG.height_mm == pytest.approx(0.0, abs=1e-9)


def test_feed_scrolls_to_next_post():
    feed = PhoneFeed(CFG.texture_shape, previous=_post(0.2))
    feed.show(_post(1.0))
    feed.update(0.0)
    top, bottom, left, right = post_box(CFG.texture_shape)
    assert np.all(feed.frame()[top:bottom, left:right] == 255)
    feed.scroll_to(_post(0.0), now_ms=0.0)
    assert feed.update(SCROLL_MS / 4) and feed.scrolling
    middle = feed.frame()[top:bottom, left:right]
    assert (middle == 255).any() and (middle < 255).any()
    feed.update(SCROLL_MS + 1)
    assert not feed.scrolling
    assert np.all(feed.frame()[top:bottom, left:right] == 0)
    assert not feed.update(SCROLL_MS + 10)


@pytest.fixture(scope="module")
def scene_body():
    from flybrain.body.body import Body
    from flybrain.body.sight import FlyEyes
    from flybrain.connectome.connectome import load_connectome
    from flybrain.senses.eye import Eye

    conn = load_connectome()
    eye = Eye(conn)
    body = Body(scene=CFG)
    body.step(np.zeros(len(body.dofs)), 2000)
    body.scene.snap()
    eyes = FlyEyes(body.sim, body.fly.name, "c_head", conn, VISION, eye)
    body.scene.register(eyes.renderer)
    yield body, eyes, eye
    eyes.close()
    body.close()


def _lum(eyes) -> dict[str, np.ndarray]:
    values = eyes.column_values()
    return {g[0]: values[g[0]]["lum"] for g in eyes.groups}


def test_left_eye_sees_left_half_of_screen(scene_body):
    body, eyes, eye = scene_body
    h, w = CFG.texture_shape
    img = np.zeros((h, w, 3), np.uint8)
    img[:, : w // 2] = 255
    body.scene.show(img)
    lum = _lum(eyes)
    name, idx, *_ = eyes.groups[0]
    _, side, phi, theta = eye.neuron_directions(idx)
    ahead = (phi > 20) & (phi < 80) & (theta > 0) & (theta < 40)  # yan ile ön arası, ufkun üstü
    left, right = lum[name][ahead & (side == "L")], lum[name][ahead & (side == "R")]
    assert np.nanmean(left) > 0.9 and np.nanmean(right) < 0.1


def test_post_covers_most_columns(scene_body):
    body, eyes, _ = scene_body
    top, bottom, left, right = post_box(CFG.texture_shape)
    img = np.zeros(CFG.texture_shape + (3,), np.uint8)
    img[top:bottom, left:right] = 255
    body.scene.show(img)
    lum = _lum(eyes)
    seen = sum(int(np.nansum(v > 0.75)) for v in lum.values())
    total = sum(len(v) for v in lum.values())
    assert seen / total > 0.55


def test_screen_follows_fly_with_lag(scene_body):
    import mujoco as mj

    body, _, _ = scene_body
    scene = body.scene
    pos0, _ = scene.pose
    m, d = body.sim.mj_model, body.sim.mj_data
    qpos = d.qpos.copy()
    free = m.jnt_qposadr[list(m.jnt_type).index(mj.mjtJoint.mjJNT_FREE)]
    d.qpos[free] += 1.0  # sineği 1 mm ileri taşı
    mj.mj_kinematics(m, d)
    scene.follow(CFG.follow_ms)
    pos1, _ = scene.pose
    assert pos1[0] - pos0[0] == pytest.approx(1.0 - np.exp(-1.0), abs=0.02)
    for _ in range(20):
        scene.follow(CFG.follow_ms)
    assert scene.pose[0][0] - pos0[0] == pytest.approx(1.0, abs=0.01)
    d.qpos[:] = qpos
    mj.mj_kinematics(m, d)
    scene.snap()
    assert scene.pose[0] == pytest.approx(pos0, abs=1e-9)


def test_fade_blends_old_and_new_screen():
    feed = PhoneFeed(CFG.texture_shape)
    feed.show(_post(1.0))
    feed.update(0.0)
    top, bottom, left, right = post_box(CFG.texture_shape)
    feed.fade_to(_post(0.0), now_ms=0.0, duration_ms=100.0)
    feed.update(50.0)
    assert np.all(np.abs(feed.frame()[top:bottom, left:right].astype(int) - 128) <= 1)
    feed.update(101.0)
    assert not feed.scrolling and np.all(feed.frame()[top:bottom, left:right] == 0)


def test_video_plays_on_post_image_and_keeps_last_frame():
    feed = PhoneFeed(CFG.texture_shape)
    feed.show(_post(1.0))
    feed.update(0.0)
    top, bottom, left, right = post_box(CFG.texture_shape)

    def video(t):
        return None if t > 20 else np.full(feed.image_shape + (3,), int(t), np.uint8)

    feed.play(video, now_ms=0.0)
    assert feed.update(10.0)
    assert np.all(feed.frame()[top:bottom, left:right] == 10)
    feed.update(30.0)
    assert np.all(feed.frame()[top:bottom, left:right] == 10)
    assert feed.frame()[top - 5, left + 5].tolist() == [255, 255, 255]  # kullanıcı satırı değişmez


def test_looming_disc_triggers_giant_fiber():
    """Yaklaşan disk (l/v 40 ms) dev lifi ateşletir ve sinek sıçrar (Z-25)."""
    from flybrain.body.embodied import EMBODIED_VISION, EmbodiedFly
    from flybrain.body.phone import fit
    from flybrain.body.scene import pixel_directions
    from flybrain.experiments.escape import HOLD_MS, JUMP_MM, looming_video
    from flybrain.experiments.scene import _Counter, _groups, _post

    fly = EmbodiedFly(vision=EMBODIED_VISION, scene=CFG, seed=1)
    counter = _Counter(fly, _groups(fly))
    top, bottom, left, right = post_box(CFG.texture_shape)
    rows, cols = np.mgrid[top:bottom, left:right]
    post = _post(0)
    fly.show_post(post)
    fly.reset()
    fly.run(300)
    t_event = fly.brain.time_ms
    counter.log.clear()
    video, t_coll = looming_video(fit(post.image, right - left, bottom - top), pixel_directions(CFG, rows, cols))
    fly.play_video(video)
    trace = fly.run(t_coll + HOLD_MS)
    w = counter.window(t_event, fly.brain.time_ms)
    thorax = trace.arrays()["thorax"]
    assert w["lc4"] > 50 and w["dev_lif"] > 0
    assert np.linalg.norm(thorax[-1] - thorax[0]) > JUMP_MM
    fly.eyes.close()
    fly.body.close()
