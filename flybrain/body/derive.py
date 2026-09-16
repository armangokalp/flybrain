"""Kas geometrisini anatomik modellerden çıkarır ve muscle_geometry.json'a yazar.

Kaynaklar:
  - Bacak kasları: FlyGym'in kas-iskelet modeli (FlyMimic; sol ön bacakta 15 kas,
    X-ray tomografisinden). Her kasın eklem serbestlik derecesi başına moment kolu
    (d uzunluk / d açı), nötr pozda sayısal türevle hesaplanır. En büyük kuvvetler
    (F0) ve eklemlerin pasif özellikleri aynı dosyadan okunur.
  - Hareket yönleri (hortum ileri, tarsus aşağı, baş sola, kanat dışa, karın aşağı):
    NeuroMechFly'ın nötr pozunda küçük bir açı değişiminin ilgili gövde parçasını
    nereye taşıdığına bakılarak belirlenir. Böylece işaretler elle yazılmaz,
    geometriden okunur.
  - Sıçrama kası (TTM): orta bacağın ucunda ölçülen 101 µN tepe kuvveti
    (Zumstein ve ark. 2004), nötr pozdaki kaldıraç koluyla torka çevrilir.

Kullanım:
    python -m flybrain.body.derive
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco as mj
import numpy as np

from flygym import assets_dir

MUSCULOSKELETAL_XML = assets_dir / "model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml"
OUT = Path(__file__).with_name("muscle_geometry.json")

# Kas-iskelet modelindeki eklem → NeuroMechFly eklem anahtarı. İki model aynı eksen
# düzenini kullanıyor (eksenler ve nötr açılar yakın); trokanter yaw'ın NeuroMechFly'da
# karşılığı yok, bu bileşen atılır ve dosyaya ayrıca yazılır.
MS_TO_NMF = {
    "joint_LFCoxa_yaw": "coxa_yaw",
    "joint_LFCoxa_pitch": "coxa_pitch",
    "joint_LFCoxa_roll": "coxa_roll",
    "joint_LFTrochanter_pitch": "trochanter_pitch",
    "joint_LFTrochanter_roll": "trochanter_roll",
    "joint_LFTibia_pitch": "tibia_pitch",
}
MS_DROPPED = ["joint_LFTrochanter_yaw"]

TTM_TIP_FORCE_UN = 101.0  # Zumstein ve ark. 2004, orta bacak ucunda tepe kuvvet
TTM_RISE_MS = 8.2         # aynı çalışma, tepeye ulaşma süresi


def _load_musculoskeletal() -> tuple[mj.MjModel, mj.MjData]:
    """Modeli 3D ağlar olmadan yükler: tendonlar düz çizgi, ağlara ihtiyaç yok."""
    root = ET.parse(MUSCULOSKELETAL_XML).getroot()
    asset = root.find("asset")
    for m in list(asset):
        if m.tag == "mesh":
            asset.remove(m)
    for parent in root.iter():
        for g in list(parent):
            if g.tag == "geom" and "mesh" in g.attrib:
                parent.remove(g)
    model = mj.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    data = mj.MjData(model)
    data.qpos[:] = model.qpos_spring
    mj.mj_forward(model, data)
    return model, data


def _tendon_arm(model, qpos, tendon: int, qadr: int, h: float = 1e-4) -> float:
    d = mj.MjData(model)
    out = []
    for s in (+h, -h):
        d.qpos[:] = qpos
        d.qpos[qadr] += s
        mj.mj_forward(model, d)
        out.append(d.ten_length[tendon])
    return (out[0] - out[1]) / (2 * h)


def leg_muscles() -> dict:
    model, data = _load_musculoskeletal()
    joints = {n: mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, n) for n in [*MS_TO_NMF, *MS_DROPPED]}
    muscles = {}
    for a in range(model.nu):
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_ACTUATOR, a)
        tendon = int(model.actuator_trnid[a, 0])
        arms = {}
        dropped = {}
        for jn, j in joints.items():
            v = _tendon_arm(model, data.qpos, tendon, int(model.jnt_qposadr[j]))
            if jn in MS_TO_NMF:
                arms[MS_TO_NMF[jn]] = round(v, 6)
            else:
                dropped[jn] = round(v, 6)
        muscles[name.removeprefix("LFC_").removeprefix("LFF_").removeprefix("LF")] = {
            "F0_uN": round(float(model.actuator_gainprm[a, 2]), 4),
            "arm_mm_per_rad": arms,
            "dropped_arm_mm_per_rad": dropped,
        }
    ranges = {}
    for jn, key in MS_TO_NMF.items():
        j = joints[jn]
        ranges[key] = {
            "range": [round(float(x), 4) for x in model.jnt_range[j]],
            "springref": round(float(model.qpos_spring[model.jnt_qposadr[j]]), 4),
        }
    j0 = joints["joint_LFTibia_pitch"]
    passive = {
        "stiffness": float(model.jnt_stiffness[j0]),
        "damping": float(model.dof_damping[model.jnt_dofadr[j0]]),
    }
    # Tibia bükme yönü: +açı femur tabanı ile tarsus arasındaki mesafeyi kısaltıyor mu?
    flex_sign = _flexion_sign_ms(model, data)
    return {"muscles": muscles, "front_leg_ranges": ranges, "passive": passive, "tibia_flexion_sign_ms": flex_sign}


def _flexion_sign_ms(model, data) -> int:
    j = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, "joint_LFTibia_pitch")
    base = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, "LFFemur")
    tip = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, "LFTarsus1")
    d = mj.MjData(model)
    dist = []
    for s in (+1e-3, -1e-3):
        d.qpos[:] = data.qpos
        d.qpos[model.jnt_qposadr[j]] += s
        mj.mj_forward(model, d)
        dist.append(np.linalg.norm(d.xpos[tip] - d.xpos[base]))
    return 1 if dist[0] < dist[1] else -1


def _nmf():
    from flygym.anatomy import AxisOrder, JointPreset, Skeleton
    from flygym.compose import KinematicPosePreset, NeuroMechFly

    fly = NeuroMechFly()
    skel = Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.ALL_BIOLOGICAL)
    fly.add_joints(skel, neutral_pose=KinematicPosePreset.NEUTRAL)
    model, data = fly.compile()
    data.qpos[:] = model.qpos_spring
    mj.mj_forward(model, data)
    return model, data


def _effect(model, data, joint: str, body: str, h: float = 1e-3) -> np.ndarray:
    """+h açının gövde parçasının ağırlık merkezini dünya çerçevesinde nasıl taşıdığı."""
    j = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, joint)
    b = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, body)
    if j < 0 or b < 0:
        raise KeyError(f"{joint} / {body} bulunamadı")
    d = mj.MjData(model)
    out = []
    for s in (+h, -h):
        d.qpos[:] = data.qpos
        d.qpos[model.jnt_qposadr[j]] += s
        mj.mj_forward(model, d)
        out.append(d.xipos[b].copy())
    return (out[0] - out[1]) / (2 * h)


def _joint_pos(model, data, joint: str) -> np.ndarray:
    return data.xanchor[mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, joint)].copy()


def nmf_directions() -> dict:
    """Her işlevsel hareketin NeuroMechFly'da hangi serbestlik derecesinde, hangi işaretle olduğu."""
    model, data = _nmf()
    sign = lambda v: 1 if v > 0 else -1  # noqa: E731
    out = {}

    # Hortum: rostrum ileri (protraksiyon) → haustellum ileri gider; haustellum açılması →
    # haustellum, baş-rostrum ekleminden uzaklaşır.
    out["rostrum_protraction"] = {
        "dof": "c_head-c_rostrum-pitch",
        "sign": sign(_effect(model, data, "c_head-c_rostrum-pitch", "c_haustellum")[0]),
    }
    base = _joint_pos(model, data, "c_head-c_rostrum-pitch")
    hb = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, "c_haustellum")
    r = data.xipos[hb] - base
    eff = _effect(model, data, "c_rostrum-c_haustellum-pitch", "c_haustellum")
    out["haustellum_extension"] = {"dof": "c_rostrum-c_haustellum-pitch", "sign": sign(float(r @ eff))}

    # Baş: dünya z eksenine en yakın eksen dönmeyi yapar; + işaret başı sola (+y) çevirmeli.
    head = {}
    for ax in ("yaw", "pitch", "roll"):
        j = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, f"c_thorax-c_head-{ax}")
        head[ax] = abs(data.xaxis[j][2])
    turn = max(head, key=head.get)
    dof = f"c_thorax-c_head-{turn}"
    out["head_turn_left"] = {"dof": dof, "sign": sign(_effect(model, data, dof, "c_rostrum")[1])}

    # Kanat: kanadın ağırlık merkezini en çok yana taşıyan eksen açma eksenidir;
    # işaret, sol kanadı dışa (+y) götürecek şekilde.
    for side, ysign in (("l", 1), ("r", -1)):
        best, best_dy = None, 0.0
        for ax in ("yaw", "pitch", "roll"):
            dy = _effect(model, data, f"c_thorax-{side}_wing-{ax}", f"{side}_wing")[1] * ysign
            if abs(dy) > abs(best_dy):
                best, best_dy = ax, dy
        out[f"{side}_wing_extension"] = {"dof": f"c_thorax-{side}_wing-{best}", "sign": sign(best_dy)}

    # Karın: her segment ekleminde uç segmentin (abdomen6) aşağı gitmesi = ventral bükülme;
    # yana bükülme için +y yönü (sola).
    chain = ["c_thorax", "c_abdomen12", "c_abdomen3", "c_abdomen4", "c_abdomen5", "c_abdomen6"]
    flex, lateral = [], []
    for p, c in zip(chain[:-1], chain[1:]):
        dz = {ax: _effect(model, data, f"{p}-{c}-{ax}", "c_abdomen6")[2] for ax in ("yaw", "pitch", "roll")}
        ax = max(dz, key=lambda k: abs(dz[k]))
        flex.append({"dof": f"{p}-{c}-{ax}", "sign": -sign(dz[ax])})
        dy = {k: _effect(model, data, f"{p}-{c}-{k}", "c_abdomen6")[1] for k in ("yaw", "pitch", "roll") if k != ax}
        axl = max(dy, key=lambda k: abs(dy[k]))
        lateral.append({"dof": f"{p}-{c}-{axl}", "sign": sign(dy[axl])})
    out["abdomen_ventral_flexion"] = flex
    out["abdomen_bend_left"] = lateral

    # Bacaklar: tibia bükülmesi femur tabanı ile tarsus arasındaki mesafeyi kısaltır
    # (tibia nötr pozda belirgin bükülü olduğu için bu ölçüt güvenilir). Tarsus nötr pozda
    # neredeyse düz; mesafe ölçütü orada işaret veremez. Böcek bacağında tarsusun aşağı
    # bükülmesi tibia bükülmesiyle aynı dönme yönündedir ve iki eklemin ekseni aynı, bu
    # yüzden aynı işaret kullanılır (eksenlerin paralelliği ayrıca kontrol edilir).
    legs = {}
    for leg in ("lf", "lm", "lh", "rf", "rm", "rh"):
        tib = f"{leg}_trochanterfemur-{leg}_tibia-pitch"
        tar = f"{leg}_tibia-{leg}_tarsus1-pitch"
        femur_base = _joint_pos(model, data, f"{leg}_coxa-{leg}_trochanterfemur-pitch")
        t1 = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, f"{leg}_tarsus1")
        e_tib = _effect(model, data, tib, f"{leg}_tarsus1")
        flex = -sign(float((data.xipos[t1] - femur_base) @ e_tib))
        a_tib = data.xaxis[mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, tib)]
        a_tar = data.xaxis[mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, tar)]
        if a_tib @ a_tar < 0.99:
            raise ValueError(f"{leg}: tibia ve tarsus eksenleri paralel değil ({a_tib @ a_tar:.3f})")
        legs[leg] = {"tibia_flexion_sign": flex, "tarsus_depression_sign": flex}
    out["legs"] = legs

    # Sıçrama: orta bacak trokanter ekleminden bacak ucuna kaldıraç kolu (eksene dik).
    lever = {}
    for leg in ("lm", "rm"):
        j = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, f"{leg}_coxa-{leg}_trochanterfemur-pitch")
        axis = data.xaxis[j]
        v = data.xipos[mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, f"{leg}_tarsus5")] - data.xanchor[j]
        lever[leg] = float(np.linalg.norm(v - (v @ axis) * axis))
    out["ttm"] = {
        "tip_force_uN": TTM_TIP_FORCE_UN,
        "rise_ms": TTM_RISE_MS,
        "lever_mm": {k: round(v, 4) for k, v in lever.items()},
        "torque_uNmm": round(TTM_TIP_FORCE_UN * float(np.mean(list(lever.values()))), 3),
    }
    out["neutral_angles"] = {
        mj.mj_id2name(model, mj.mjtObj.mjOBJ_JOINT, j): round(float(data.qpos[model.jnt_qposadr[j]]), 4)
        for j in range(model.njnt)
        if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
    }
    return out


def main():
    geom = {"source": {
        "leg_muscles": "flygym/assets/model/musculoskeletal (FlyMimic), nötr poz, sayısal türev",
        "ttm": "Zumstein ve ark. 2004, J Exp Biol 207:3515",
        "directions": "NeuroMechFly (flygym 2.1) nötr pozunda geometri",
    }}
    geom.update(leg_muscles())
    geom["nmf"] = nmf_directions()
    OUT.write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    print(f"yazıldı: {OUT}")
    print("tibia bükme işareti (kas-iskelet modeli):", geom["tibia_flexion_sign_ms"])
    for k, v in geom["nmf"].items():
        if k not in ("neutral_angles",):
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
