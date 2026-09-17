"""Oturum kaydı ve yeniden çizim (Faz 6)."""

import imageio.v2 as imageio
import numpy as np
import pytest

from flybrain.connectome.build import WEIGHTS

pytestmark = pytest.mark.skipif(not WEIGHTS.exists(), reason="ham veri yok")


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    from flybrain.experiments.calibrate import TEST_SEED, make_post
    from flybrain.experiments.embodied_calibrate import _viewer
    from flybrain.motor.selector import CALIBRATION_EMBODIED_PATH, Calibration
    from flybrain.viz.record import SessionRecorder, load

    viewer = _viewer(8003, Calibration.load(CALIBRATION_EMBODIED_PATH))
    fly = viewer.fly
    path = tmp_path_factory.mktemp("kayit") / "oturum"
    rec = SessionRecorder(fly, path)
    decisions = [viewer.look(make_post(70_000 + k, TEST_SEED)) for k in range(2)]
    counts = viewer.counts.copy()
    post_start = [e["t_ms"] for e in rec.events if e["tur"] == "post"][-1]
    thorax = fly.body.state().thorax_pos.copy()
    screen = fly.scene.pose
    rec.close()
    assert fly.recorder is None
    yield load(path), decisions, counts, post_start, thorax, screen
    fly.eyes.close()
    fly.body.close()


def test_recording_layout_and_events(session):
    rec, decisions, *_ = session
    meta, off = rec["meta"], rec["spikes"]["ofset"]
    assert len(off) == meta["sure_ms"] + 1 and np.all(np.diff(off.astype(np.int64)) >= 0)
    assert off[-1] == len(rec["spikes"]["noron"]) == meta["spike_sayisi"] > 0
    assert rec["spikes"]["noron"].max() < meta["noron_sayisi"]
    g = rec["govde"]
    assert g["qpos"].shape == (meta["sure_ms"] // meta["govde_araligi_ms"], meta["nq"])
    assert np.all(np.diff(g["t_ms"]) == meta["govde_araligi_ms"])
    kinds = [e["tur"] for e in rec["olaylar"]]
    assert kinds.count("post") == 2 and kinds.count("karar") == 2
    karar = [e for e in rec["olaylar"] if e["tur"] == "karar"]
    assert [e["eylem"] for e in karar] == [d.action for d in decisions]
    assert all(e["sure_ms"] == d.dwell_ms for e, d in zip(karar, decisions))


def test_recorded_spikes_match_decision_readout(session):
    """Son postun karar okumasındaki spike sayaçları kayıttaki spike'larla birebir aynı."""
    from flybrain.viz.record import spikes_between

    rec, _, counts, post_start, *_ = session
    idx = spikes_between(rec, post_start, rec["meta"]["sure_ms"])
    assert np.array_equal(np.bincount(idx, minlength=len(counts)), counts)


def test_videos_have_one_frame_per_recorded_time(session):
    rec, *_ = session
    n = len(rec["kareler"]["t_ms"])
    assert n == rec["meta"]["sure_ms"] // rec["meta"]["kare_araligi_ms"]
    for name in ("ekran", "gozler"):
        reader = imageio.get_reader(rec["yol"] / f"{name}.mp4")
        assert reader.count_frames() == n
        h, w = reader.get_data(0).shape[:2]
        assert (h, w) == (rec["meta"]["videolar"][name]["yukseklik"], rec["meta"]["videolar"][name]["genislik"])
        reader.close()


def test_replay_rebuilds_final_pose(session):
    from flybrain.viz.replay import Replay

    rec, _, _, _, thorax, (screen_pos, screen_yaw) = session
    rp = Replay(rec, 160, 120)
    try:
        rp.pose(rec["meta"]["sure_ms"])
        assert np.allclose(rp.thorax(), thorax, atol=1e-4)
        mocap = rp.d.mocap_pos[0]
        assert np.allclose(mocap[:2], screen_pos, atol=1e-4)  # telefon ekranı da sineğin önünde
        w, z = rp.d.mocap_quat[0][[0, 3]]
        assert abs(np.angle(np.exp(1j * (2 * np.arctan2(z, w) - screen_yaw)))) < 1e-4
        img = rp.render(rec["meta"]["sure_ms"])
        assert img.shape == (120, 160, 3) and img.std() > 5
        frames = rp.body_frames()
        assert frames["pos"].shape[0] == len(rec["govde"]["t_ms"])
    finally:
        rp.close()


def test_web_export_is_consistent(session):
    import json

    from flybrain.viz.export import export

    rec, *_ = session
    out = export(rec["yol"])
    scene = json.loads((out / "sahne.json").read_text())
    brain = json.loads((out / "noronlar.json").read_text())
    parts, frames = scene["parcalar"], scene["kare"]
    size = lambda name: (out / name).stat().st_size
    assert size("kare.bin") == frames["sayi"] * len(parts) * 7 * 4
    assert size("geo_kose.bin") == 4 * 3 * sum(p["kose"][1] for p in parts)
    assert size("geo_yuz.bin") == 4 * sum(p["yuz"][1] for p in parts)
    assert size("noron_konum.bin") == 4 * 3 * brain["sayi"]
    assert size("spike_noron.bin") == 4 * rec["meta"]["spike_sayisi"]
    assert sum(p["doku"] == "ekran" for p in parts) == 1
    kinds = {p["govde"].split("/")[-1]: p["kasli"] for p in parts}
    assert kinds["lf_tarsus5"] == "lf_tarsus1" and kinds["c_thorax"] is None
    assert all(len(v) for v in brain["kanallar"].values())
    pos = np.fromfile(out / "noron_konum.bin", np.float32)
    assert np.isfinite(pos).all()


def test_short_video_renders(session, tmp_path):
    from flybrain.viz.video import export_video

    rec, *_ = session
    out = export_video(rec["yol"], tmp_path / "v.mp4", speed=0.5, end_ms=200)
    reader = imageio.get_reader(out)
    assert reader.count_frames() == 12 and reader.get_data(0).shape == (720, 1280, 3)
    reader.close()
