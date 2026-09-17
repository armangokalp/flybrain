"""Oturum kaydını tarayıcı paneli için dışa aktarır (Faz 6).

Çıktı kaydın içindeki web/ dizinidir; panel bu dosyaları ve kaydın videolarını okur:
  sahne.json          geometri parçaları (ad, tür, renk, dizi aralıkları), kare zamanları
  geo_kose.bin        float32 köşe konumları (parçanın kendi çerçevesinde, mm)
  geo_yuz.bin         uint32 üçgen indeksleri (parçanın köşelerine göre)
  geo_uv.bin          float32 doku koordinatları (yalnızca telefon ekranı, köşe başına)
  kare.bin            float32 [kare, parça, 7]: konum (3) + dörtlü (w, x, y, z), GOVDE_ADIMI_MS'de bir
  noron_konum.bin     float32 [nöron, 3], µm, beyin merkezine göre
  noron_sinif.bin     uint8 [nöron]: sınıf kodu (noronlar.json'daki sırayla)
  noron_yaklasik.bin  uint8 [nöron]: 1 ise konum yaklaşık (aşağıda)
  noronlar.json       sınıf adları, kanal nöronları, konum notu
  spike_ofset.bin     uint32: i. milisaniyenin spike'ları noron[ofset[i]:ofset[i+1]]
  spike_noron.bin     uint32 nöron indeksleri

Nöron konumları MaleCNS soma konumlarıdır (8 nm voksel → µm). Somasız nöronların (çoğu duyu
nöronu ve optik lob iç nöronu, ~%15) konumu VARSAYIM: bağlantılı oldukları nöronların
konumlarının sinaps sayısıyla ağırlıklı ortalaması. Panel bu nöronları ayrıca işaretler.

Kullanım:
    python -m flybrain.viz.export runs/oturum-<ad>
"""

import argparse
import json
from pathlib import Path

import mujoco as mj
import numpy as np
from scipy.spatial.transform import Rotation

from flybrain.viz.record import load
from flybrain.viz.replay import SCREEN_BODY, Replay

GOVDE_ADIMI_MS = 10
VOXEL_UM = 0.008  # MaleCNS koordinatları 8 nm vokselde
VISIBLE_GROUPS = (0, 1, 2)  # MuJoCo'nun varsayılan olarak çizdiği gruplar


def _geom_color(m: mj.MjModel, g: int) -> list[float]:
    mat = m.geom_matid[g]
    if mat < 0:
        return [float(x) for x in m.geom_rgba[g]]
    rgba = m.mat_rgba[mat].astype(float).copy()
    tex = m.mat_texid[mat][1]  # RGB yuvası
    if tex >= 0:
        a, w, h, c = m.tex_adr[tex], m.tex_width[tex], m.tex_height[tex], m.tex_nchannel[tex]
        rgba[:3] *= m.tex_data[a:a + w * h * c].reshape(-1, c)[:, :3].mean(0) / 255.0
    return [float(x) for x in rgba]


def muscle_map(conn, rp: Replay) -> tuple[dict, dict]:
    """Kaslar (ad → hareket ettirdiği gövde parçası, motor nöronlar) ve her gövde parçası için
    kaslı en yakın parça (kendisi ya da atası). Bir eklemin adındaki ikinci parça, eklemin
    hareket ettirdiği gövde parçasıdır (ör. lf_trochanterfemur-lf_tibia-pitch → lf_tibia)."""
    from flybrain.body.muscles import build_table

    table = build_table(conn, rp.body.passive)
    muscles = {}
    for mus in table.muscles:
        parts = sorted({d.split("-")[1] for d in mus.torque})
        muscles[mus.name] = {"govde": parts, "mn": [int(i) for i in mus.mn]}
    moved = {p_ for v in muscles.values() for p_ in v["govde"]}
    m = rp.m
    prefix = rp.body.fly.name + "/"
    nearest = {}
    for b in range(m.nbody):
        name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, b) or ""
        if not name.startswith(prefix):
            continue
        a = b
        while a > 0:
            short = (mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, a) or "").removeprefix(prefix)
            if short in moved:
                nearest[name] = short
                break
            a = m.body_parentid[a]
    return muscles, nearest


def export_scene(rp: Replay, out: Path, nearest: dict | None = None) -> dict:
    m = rp.m
    nearest = nearest or {}
    body_name = lambda g: mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) or ""
    fly_prefix = rp.body.fly.name + "/"
    parts, verts, faces, uvs = [], [], [], []
    nv = nf = nuv = 0
    geoms = []
    for g in range(m.ngeom):
        name = body_name(g)
        kind = "sinek" if name.startswith(fly_prefix) else ("ekran" if name == SCREEN_BODY else None)
        if kind is None or m.geom_group[g] not in VISIBLE_GROUPS or m.geom_type[g] != mj.mjtGeom.mjGEOM_MESH:
            continue
        mesh = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh] + m.mesh_vertnum[mesh]]
        f = m.mesh_face[m.mesh_faceadr[mesh]:m.mesh_faceadr[mesh] + m.mesh_facenum[mesh]]
        textured = kind == "ekran" and m.geom_matid[g] >= 0 and m.mesh_texcoordnum[mesh] > 0
        if textured:  # doku koordinatları köşe başına değil yüz köşesi başına: üçgenleri aç
            tc = m.mesh_texcoord[m.mesh_texcoordadr[mesh]:m.mesh_texcoordadr[mesh] + m.mesh_texcoordnum[mesh]]
            ft = m.mesh_facetexcoord[m.mesh_faceadr[mesh]:m.mesh_faceadr[mesh] + m.mesh_facenum[mesh]]
            v, uv, f = v[f.reshape(-1)], tc[ft.reshape(-1)], np.arange(f.size).reshape(-1, 3)
            uvs.append(uv.astype(np.float32))
        part = {
            "ad": mj.mj_id2name(m, mj.mjtObj.mjOBJ_MESH, mesh), "govde": name, "tur": kind,
            "renk": _geom_color(m, g), "doku": "ekran" if textured else None, "kasli": nearest.get(name),
            "kose": [nv, len(v)], "yuz": [nf, int(f.size)], "uv": [nuv, len(v)] if textured else None,
        }
        verts.append(v.astype(np.float32))
        faces.append(f.astype(np.uint32).reshape(-1))
        nv += len(v)
        nf += f.size
        nuv += len(v) if textured else 0
        parts.append(part)
        geoms.append(g)
    np.concatenate(verts).tofile(out / "geo_kose.bin")
    np.concatenate(faces).tofile(out / "geo_yuz.bin")
    (np.concatenate(uvs) if uvs else np.zeros((0, 2), np.float32)).tofile(out / "geo_uv.bin")

    step = max(1, GOVDE_ADIMI_MS // rp.rec["meta"]["govde_araligi_ms"])
    rows = np.arange(0, len(rp.t_ms), step)
    frames = np.zeros((len(rows), len(geoms), 7), np.float32)
    for k, i in enumerate(rows):
        rp.set_state(i)
        mj.mj_kinematics(rp.m, rp.d)
        frames[k, :, :3] = rp.d.geom_xpos[geoms]
        xyzw = Rotation.from_matrix(rp.d.geom_xmat[geoms].reshape(-1, 3, 3)).as_quat()
        frames[k, :, 3] = xyzw[:, 3]
        frames[k, :, 4:] = xyzw[:, :3]
    frames.tofile(out / "kare.bin")
    return {
        "parcalar": parts,
        "kare": {"sayi": len(rows), "t_ms": [float(rp.t_ms[i]) for i in rows[[0, -1]]],
                 "adim_ms": float(step * rp.rec["meta"]["govde_araligi_ms"])},
        "tutuluyor": rp.held[rows].astype(int).tolist(),
    }


def neuron_positions(conn) -> tuple[np.ndarray, np.ndarray]:
    """µm cinsinden konumlar ve yaklaşık konum işareti (somasız nöronlar)."""
    xyz = conn.neurons[["soma_x", "soma_y", "soma_z"]].to_numpy(float) * VOXEL_UM
    known = ~np.isnan(xyz).any(axis=1)
    approx = ~known
    A = abs(conn.W).astype(np.float64)
    A = (A + A.T).tocsr()
    pos = np.where(known[:, None], xyz, 0.0)
    have = known.astype(float)
    for _ in range(3):  # bağlantılıların da konumu yoksa birkaç turda yayılır
        missing = have == 0
        if not missing.any():
            break
        wsum = A @ have
        est = (A @ (pos * have[:, None])) / np.maximum(wsum, 1e-9)[:, None]
        fill = missing & (wsum > 0)
        pos[fill] = est[fill]
        have[fill] = 1.0
    pos[have == 0] = np.nanmean(xyz, axis=0)
    center = np.nanmean(xyz[known], axis=0)
    return (pos - center).astype(np.float32), approx


def export_brain(conn, rec: dict, out: Path, muscles: dict | None = None) -> dict:
    from flybrain.motor.readout import MotorReadout

    pos, approx = neuron_positions(conn)
    pos.tofile(out / "noron_konum.bin")
    approx.astype(np.uint8).tofile(out / "noron_yaklasik.bin")
    sc = conn.neurons["superclass"].fillna("bilinmiyor").astype(str)
    classes = sorted(sc.unique())
    code = {c: i for i, c in enumerate(classes)}
    np.array([code[c] for c in sc], np.uint8).tofile(out / "noron_sinif.bin")
    ro = MotorReadout(conn)
    channels = {k: [int(i) for i in v] for k, v in ro.groups.items()}
    channels["sekme"] = [int(i) for i in np.r_[ro.neck_left, ro.neck_right]]
    channels["timar"] = [int(i) for i in ro.front_legs]
    rec["spikes"]["ofset"].astype(np.uint32).tofile(out / "spike_ofset.bin")
    rec["spikes"]["noron"].astype(np.uint32).tofile(out / "spike_noron.bin")
    return {
        "sayi": int(conn.n), "siniflar": classes, "kanallar": channels, "kaslar": muscles or {},
        "yaklasik_sayi": int(approx.sum()),
        "konum_notu": "Somasız nöronların konumu yaklaşık: bağlantılı nöronların ağırlıklı ortalaması.",
        "tip": conn.neurons["type"].fillna("").astype(str).tolist(),
    }


def export(path: str | Path) -> Path:
    from flybrain.connectome.connectome import load_connectome

    rec = load(path)
    out = Path(path) / "web"
    out.mkdir(exist_ok=True)
    conn = load_connectome()
    rp = Replay(rec, 64, 48)
    try:
        muscles, nearest = muscle_map(conn, rp)
        scene = export_scene(rp, out, nearest)
    finally:
        rp.close()
    brain = export_brain(conn, rec, out, muscles)
    (out / "sahne.json").write_text(json.dumps(scene, ensure_ascii=False))
    (out / "noronlar.json").write_text(json.dumps(brain, ensure_ascii=False))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kayit")
    out = export(ap.parse_args().kayit)
    size = sum(f.stat().st_size for f in out.iterdir()) / 1e6
    print(f"dışa aktarıldı: {out} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
