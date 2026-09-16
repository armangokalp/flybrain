"""Propriyosepsiyon doğrulamaları.

  imza    : FeCO tiplerinin bükülme/açılma ataması, Lee ve ark. (2025) bağlantı imzasına
            uyuyor mu? Bükülme algılayıcısı tibia açıcı motor nöronlarını doğrudan uyarır,
            bükücüleri ara nöronlar üzerinden ketler; açılma algılayıcısı tersini yapar.
  refleks : bacak dışarıdan (deneycinin probu gibi) bükülür ya da açılır; direnç refleksi
            varsa bükme açıcı, açma bükücü motor nöronlarını ateşletir. Propriyosepsiyon
            kapalıyken aynı deney kontrol olarak tekrarlanır.

Kullanım:
    python -m flybrain.experiments.proprio [--workers 6]
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from flybrain.paths import RUNS

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
PROBE_GAIN = 2.0     # µN·mm/rad; bacağın pasif sertliğinin (0,4) 5 katı
PROBE_AMP = 0.5      # rad
PROBE_RAMP_MS = 50.0
BASE_MS, PROBE_MS, POST_MS = 300, 400, 200


def signature() -> list[dict]:
    """Her FeCO tipi için tibia motor nöronlarına doğrudan ve iki adımlı etki (tüm bacaklar)."""
    from flybrain.body.muscles import build_table
    from flybrain.body.proprio import FECO, NERVE_LEG
    from flybrain.connectome.connectome import load_connectome

    conn = load_connectome()
    nn = conn.neurons
    t = nn.type.fillna("").astype(str).to_numpy(dtype=object)
    side = nn.side.fillna("").astype(str).to_numpy(dtype=object)
    leg_of = np.array([NERVE_LEG.get(x, "") for x in nn.entryNerve.fillna("").astype(str)], dtype=object)
    table = build_table(conn, {"leg": 0.4, "other": 10.0})
    mn_of = {m.name: m.mn for m in table.muscles}
    W = conn.W.tocsc()
    Wr = conn.W.tocsr()
    in_total = np.asarray(abs(W).sum(axis=1)).ravel()
    motor = np.zeros(conn.n, dtype=bool)
    motor[np.concatenate([m.mn for m in table.muscles])] = True
    rows = []
    for ty, (label, kind, direction) in FECO.items():
        if kind == "speed":
            continue
        tot = {"dogrudan_acici": 0.0, "dogrudan_bukucu": 0.0, "iki_adim_acici": 0.0, "iki_adim_bukucu": 0.0}
        for leg in LEGS:
            idx = np.flatnonzero((t == ty) & (side == leg[0].upper()) & (leg_of == leg[1]))
            if len(idx) == 0:
                continue
            out = np.asarray(W[:, idx].sum(axis=1)).ravel()
            # iki adım: duyu → ara nöron (ara nöronun girdisindeki payı) → motor nöron
            frac = np.where(motor, 0.0, out / np.maximum(in_total, 1))
            two = Wr @ frac
            for muscle, key in (("Tibia_extensor_93932", "acici"), ("Tibia_flex_93434", "bukucu")):
                mn = mn_of[f"{leg}:{muscle}"]
                tot[f"dogrudan_{key}"] += out[mn].sum()
                tot[f"iki_adim_{key}"] += two[mn].sum()
        expect_flexion = direction > 0
        fits = (tot["dogrudan_acici"] > tot["dogrudan_bukucu"]) == expect_flexion and \
               (tot["iki_adim_bukucu"] < tot["iki_adim_acici"]) == expect_flexion
        rows.append({"tip": ty, "atama": label, **{k: round(v, 1) for k, v in tot.items()}, "imzaya_uyuyor": bool(fits)})
    return rows


def reflex(leg: str, proprio: bool, seed: int = 0) -> list[dict]:
    from flybrain.body.embodied import EmbodiedFly

    fly = EmbodiedFly(seed=seed, proprioception=proprio)
    dofs = fly.body.dofs
    j = dofs.index(f"{leg}_trochanterfemur-{leg}_tibia-pitch")
    jn = fly.joint(dofs[j])
    flex_sign = fly.body.geom["nmf"]["legs"][leg]["tibia_flexion_sign"]
    mn = fly.muscles.mn
    ext = np.isin(mn, next(m.mn for m in fly.table.muscles if m.name == f"{leg}:Tibia_extensor_93932"))
    flx = np.isin(mn, next(m.mn for m in fly.table.muscles if m.name == f"{leg}:Tibia_flex_93434"))
    out = []
    for direction, label in ((+1, "bukme"), (-1, "acma")):
        fly.reset()
        th0 = fly.body.dof_angles()[j]
        clock = {"ms": 0.0}

        def probe(f):
            clock["ms"] += 1.0
            target = th0 + direction * flex_sign * PROBE_AMP * min(1.0, clock["ms"] / PROBE_RAMP_MS)
            tau = np.zeros(len(dofs))
            tau[j] = PROBE_GAIN * (target - f.body.dof_angles()[j])
            f.body.apply_external(tau)

        tr = fly.run(BASE_MS, record_every_ms=1)
        nb = len(tr.t_ms)
        fly.run(PROBE_MS, trace=tr, record_every_ms=1, on_step=probe)
        npb = len(tr.t_ms)
        fly.body.apply_external(None)
        fly.run(POST_MS, trace=tr, record_every_ms=1)
        a = tr.arrays()
        sp = a["mn_spikes"]
        per_s = lambda sel, s: float(sp[s][:, sel].sum() / ((s.stop - s.start) / 1000))  # noqa: E731
        base, during = slice(0, nb), slice(nb, npb)
        ang = a["angles"][:, jn]
        out.append({
            "bacak": leg, "propriyo": proprio, "yon": label,
            "aci_degisimi_rad": round(float(flex_sign * (ang[during].mean() - th0)), 3),
            "acici_hz_once": round(per_s(ext, base), 1), "acici_hz_prob": round(per_s(ext, during), 1),
            "bukucu_hz_once": round(per_s(flx, base), 1), "bukucu_hz_prob": round(per_s(flx, during), 1),
        })
    fly.body.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    sig = signature()
    print("FeCO bağlantı imzası (tüm bacaklar, sinaps):")
    for r in sig:
        print(" ", json.dumps(r, ensure_ascii=False))
    jobs = [(leg, p) for p in (True, False) for leg in LEGS]
    with ProcessPoolExecutor(args.workers) as ex:
        res = [r for rs in ex.map(reflex, *zip(*jobs)) for r in rs]
    print("\nDirenç refleksi (motor nöron grubu başına spike/s; prob öncesi → prob sırasında):")
    for r in res:
        print(f"  {r['bacak']} propriyo={'açık ' if r['propriyo'] else 'kapalı'} {r['yon']:5s} "
              f"açı {r['aci_degisimi_rad']:+.2f}  açıcı {r['acici_hz_once']:5.1f} → {r['acici_hz_prob']:5.1f}  "
              f"bükücü {r['bukucu_hz_once']:5.1f} → {r['bukucu_hz_prob']:5.1f}")
    path = RUNS / f"proprio-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps({"imza": sig, "refleks": res}, indent=1, ensure_ascii=False))
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
