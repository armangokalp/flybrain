"""Pugliese ve ark. (2025) ön bacak ritminin yeniden üretimi (K-025).

Ağ: yazarların MaleCNS ön bacak (T1) tablosundaki 4.309 nöron
(data/raw/pugliese/wTable_20260210_vncRoisOnly.csv). Bağlantılar bizim MaleCNS
önbelleğimizden (≥5 sinaps). Uyarım yazarların MaleCNS koşusundaki gibi
(Zenodo 22260924, DNg100_Stim_IMAC_vncOnly/logs/run_config.yaml): sağ DNg100'e
20 ms'den itibaren I = 400, süre 2 sn.

Ölçütler (yazarların tanımıyla):
  - ilk 250 ms atılır; motor modülü etiketli nöronlardan en yüksek hızı 0,01 Hz'i aşanlar etkin sayılır
  - salınım skoru: normalize öz-ilintinin sıfır dışındaki en belirgin tepesinin
    min(yükseklik, belirginlik) değeri, aynı frekanstaki sinüsün skoruna bölünür;
    etkin motor nöronların ortalaması. 0,5 ve üstü "salınıyor".
  - frekans: o tepenin gecikmesinden.
  - kalça öne itici (coxa swing) ve arkaya itici (coxa stance) motor nöronlarının faz farkı.

Karşılaştırmalar: gerçek boyut / sinaps sayısı vekili; Euler adımı 0,1 / 0,025 ms.

--bacaklar: altı bacağın motor ağı (connectome/motor_network.py), inen nöronlar kelepçeli;
DNg100 hızı × tohum taraması, bacak başına etkin ve salınan motor nöronlar.

--hibrit: aynı ağ LIF beyinle birlikte (sim/hybrid.py); DNg100'ün pürüzsüz hızı ile
spike dizisinin (farklı süzgeçlerle) karşılaştırması.

Kullanım:
    python -m flybrain.experiments.vnc_rhythm [--replicates 32] [--workers 6]
    python -m flybrain.experiments.vnc_rhythm --bacaklar
    python -m flybrain.experiments.vnc_rhythm --hibrit
"""

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from flybrain.paths import RAW, RUNS

T1_TABLE = RAW / "pugliese" / "wTable_20260210_vncRoisOnly.csv"
STIM_START_MS = 20.0
DURATION_MS = 2000.0
CLIP_MS = 250
STIM_I = 400.0
STIM = "DNg100_R"


def _score_one(x: np.ndarray, prominence: float = 0.05) -> tuple[float, float]:
    lo, hi = x.min(), x.max()
    if hi - lo <= 1e-6:
        return 0.0, 0.0
    y = 2 * (x - lo) / (hi - lo) - 1
    ac = np.correlate(y, y, "full")
    ac = ac / np.abs(ac).max()
    ac = ac[len(y) - 1:]
    peaks, props = find_peaks(ac, prominence=prominence)
    if len(peaks) == 0:
        return 0.0, 0.0
    best = np.argmax(props["prominences"])
    score = min(ac[peaks].max(), props["prominences"].max())
    return float(score), 1.0 / peaks[best]


def oscillation_score(x: np.ndarray) -> tuple[float, float]:
    """Tek bir izin (1 ms örnekli) salınım skoru ve frekansı (Hz)."""
    raw, f = _score_one(x)
    if raw <= 1e-6:
        return 0.0, 0.0
    t = np.arange(len(x))
    ref = max(_score_one(np.sin(2 * np.pi * f * t))[0], _score_one(np.cos(2 * np.pi * f * t))[0])
    return (float(np.clip(raw / ref, 0, 1)) if ref > 1e-6 else 0.0), f * 1000.0


@lru_cache(maxsize=1)
def network():
    from flybrain.connectome.connectome import load_connectome

    conn = load_connectome()
    table = pd.read_csv(T1_TABLE, index_col=0)
    # v1.0 ek açıklamalarında olmayan gövdeler atlanır (tabloda 1 tipsiz duyu nöronu).
    table = table[table.bodyId.isin(conn.neurons.bodyId)].reset_index(drop=True)
    idx = conn.index_of(table.bodyId.to_numpy())
    W = conn.W[idx][:, idx]
    tot = np.asarray(abs(conn.W).sum(axis=0)).ravel() + np.asarray(abs(conn.W).sum(axis=1)).ravel()
    return table, W, tot[idx]


def simulate(seed: int, size_source: str = "gercek", dt_ms: float = 0.1, stim: str = STIM) -> dict:
    from flybrain.sim.rate import RateNetwork, RateParams

    table, W, synapses = network()
    size = table["size"].to_numpy(float) if size_source == "gercek" else synapses.astype(float)
    net = RateNetwork(W, size, replace(RateParams(), dt_ms=dt_ms), seed=seed)
    mn = np.flatnonzero(table["motor module"].notna().to_numpy())
    current = np.zeros(net.n)
    current[np.flatnonzero(table.instance.to_numpy() == stim)] = STIM_I
    rec = [net.run(STIM_START_MS, record=mn, record_every_ms=1)]
    rec.append(net.run(DURATION_MS - STIM_START_MS, current, record=mn, record_every_ms=1))
    R = np.vstack(rec)[CLIP_MS:]
    active = R.max(axis=0) > 0.01
    scores = np.zeros(len(mn))
    freqs = np.full(len(mn), np.nan)
    for k in np.flatnonzero(active):
        scores[k], f = oscillation_score(R[:, k])
        if f > 0:
            freqs[k] = f
    score = float(scores[active].mean()) if active.any() else 0.0
    module = table["motor module"].to_numpy(dtype=object)[mn]
    side = table.somaSide.fillna("").to_numpy(dtype=object)[mn]
    phase = {}
    for s in ("L", "R"):
        sw = active & (module == "coxa swing") & (side == s)
        st = active & (module == "coxa stance") & (side == s)
        if sw.any() and st.any():
            a = R[:, sw].mean(axis=1) - R[:, sw].mean()
            b = R[:, st].mean(axis=1) - R[:, st].mean()
            f = np.nanmedian(freqs[sw | st])
            if np.isfinite(f) and f > 0 and a.std() > 0 and b.std() > 0:
                period = int(round(1000 / f))
                lags = np.arange(-period // 2, period // 2 + 1)
                cc = [np.corrcoef(a[max(0, -L):len(a) - max(0, L)], b[max(0, L):len(b) - max(0, -L)])[0, 1] for L in lags]
                phase[s] = round(float(lags[int(np.argmax(cc))] / period * 360), 1)
    return {"tohum": seed, "boyut": size_source, "dt_ms": dt_ms, "etkin_mn": int(active.sum()), "skor": round(score, 3),
            "frekans_hz": round(float(np.nanmedian(freqs[active])), 2) if np.isfinite(freqs[active]).any() else None,
            "en_yuksek_mn_hz": round(float(R.max()), 1), "kalca_faz_derece": phase,
            "iz": R[:, active][:, :8].round(2).tolist() if seed == 0 else None}


def summarize(rows: list[dict]) -> dict:
    s = np.array([r["skor"] for r in rows])
    f = np.array([r["frekans_hz"] for r in rows if r["frekans_hz"]])
    return {"n": len(rows), "salinan_oran": round(float((s >= 0.5).mean()), 3), "skor_medyan": round(float(np.median(s)), 3),
            "frekans_medyan_hz": round(float(np.median(f)), 2) if len(f) else None,
            "etkin_mn_medyan": int(np.median([r["etkin_mn"] for r in rows]))}


LEGS = ("lf", "rf", "lm", "rm", "lh", "rh")


@lru_cache(maxsize=1)
def legs_network():
    import scipy.sparse as sp

    from flybrain.connectome import motor_network
    from flybrain.connectome.connectome import load_connectome
    from flybrain.connectome.sizes import with_fallback
    from flybrain.sim.hybrid import RATE_SUPERCLASSES

    conn = load_connectome()
    nn = conn.neurons
    col = lambda c: nn[c].fillna("").astype(str).to_numpy(dtype=object)  # noqa: E731
    sup, sub, side, inst = col("superclass"), col("subclass"), col("side"), col("instance")
    members = conn.index_of(motor_network.load(conn).bodyId.to_numpy())
    dyn = members[np.isin(sup[members], RATE_SUPERCLASSES)]
    clamp = members[sup[members] == "descending_neuron"]
    idx = np.r_[dyn, clamp]
    size = with_fallback(nn)[0].to_numpy()
    W = sp.diags(np.r_[np.ones(len(dyn)), np.zeros(len(clamp))]) @ conn.W[idx][:, idx]
    dng100 = np.flatnonzero(np.isin(inst[idx], ["DNg100_L", "DNg100_R"]))
    legs = {f"{s.lower()}{c[0]}": np.flatnonzero((sup[idx] == "vnc_motor") & (sub[idx] == c) & (side[idx] == s))
            for c in ("fl", "ml", "hl") for s in "LR"}
    return W, size[idx], float(np.median(size[members])), len(dyn), dng100, legs


def _leg_scores(X: np.ndarray, legs: dict) -> dict:
    out = {}
    for leg in LEGS:
        Y = X[CLIP_MS:, legs[leg]]
        active = Y.max(axis=0) > 0.01
        sc = [oscillation_score(Y[:, k]) for k in np.flatnonzero(active)]
        out[leg] = {"etkin": int(active.sum()), "skor": round(float(np.mean([a for a, _ in sc])), 2) if sc else 0.0,
                    "en_yuksek_hz": round(float(Y.max()), 1) if Y.size else 0.0}
    return out


def legs_run(seed: int, hz: float) -> dict:
    from flybrain.sim.rate import RateNetwork

    W, size, ref, nd, dng100, legs = legs_network()
    net = RateNetwork(W, size, seed=seed, clamped=np.arange(nd, W.shape[0]), size_reference=ref)
    net.run(STIM_START_MS)
    X = net.run(DURATION_MS - STIM_START_MS, clamp_idx=dng100, clamp_hz=np.full(len(dng100), hz),
                record=np.arange(nd), record_every_ms=1)
    return {"tohum": seed, "dng100_hz": hz, "etkin": int((X.max(axis=0) > 0.01).sum()),
            "bacaklar": _leg_scores(X[:, :], {k: v for k, v in legs.items()})}


def hybrid_run(mode: str, filter_ms: float, hz: float = 17.0, seed: int = 0) -> dict:
    from flybrain.connectome.connectome import load_connectome
    from flybrain.connectome.electrical import with_electrical
    from flybrain.sim import BRAIN_PARAMS, Stimulus
    from flybrain.sim.hybrid import HybridCNS

    conn, exempt, _ = with_electrical(load_connectome(), BRAIN_PARAMS)
    nn = conn.neurons
    col = lambda c: nn[c].fillna("").astype(str).to_numpy(dtype=object)  # noqa: E731
    sup, sub, side, inst = col("superclass"), col("subclass"), col("side"), col("instance")
    d = np.flatnonzero(np.isin(inst, ["DNg100_L", "DNg100_R"]))
    cns = HybridCNS(conn, seed=seed, std_exempt=exempt, spike_filter_ms=filter_ms)
    dpos = np.searchsorted(cns.from_brain, d)
    legs = {f"{s.lower()}{c[0]}": np.flatnonzero((sup == "vnc_motor") & (sub == c) & (side == s))
            for c in ("fl", "ml", "hl") for s in "LR"}
    order = np.concatenate([legs[leg] for leg in LEGS])
    spans, k = {}, 0
    for leg in LEGS:
        spans[leg] = np.arange(k, k + len(legs[leg]))
        k += len(legs[leg])
    X = np.zeros((int(DURATION_MS), len(order)))
    stim = Stimulus.of(d, hz)
    spikes = np.zeros(2)
    for t in range(int(DURATION_MS)):
        if mode == "puruzsuz":
            cns.step(1.0, None)
            cns.spike_rate[dpos] = hz
        else:
            spikes += cns.step(1.0, stim if t >= STIM_START_MS else None)[d]
        X[t] = cns.rate.R[cns.pos[order]]
    return {"mod": mode, "suzgec_ms": filter_ms, "dng100_hz": hz,
            "dng100_gercek_hz": (spikes / (DURATION_MS / 1000)).round(1).tolist() if mode != "puruzsuz" else None,
            "etkin": int((cns.network_rates > 0.01).sum()), "bacaklar": _leg_scores(X, spans)}


def main_legs(workers: int):
    rates = [10, 12, 14, 17, 20, 25]
    jobs = [(s, r) for r in rates for s in range(8)]
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(legs_run, *zip(*jobs)))
    print("DNg100 (pürüzsüz) | etkin nöron medyanı | bacak başına: etkin MN olan / salınan (skor ≥ 0,5) tohum sayısı (8)")
    for r in rates:
        sel = [x for x in rows if x["dng100_hz"] == r]
        cells = ", ".join(f"{leg} {sum(x['bacaklar'][leg]['etkin'] > 0 for x in sel)}/"
                          f"{sum(x['bacaklar'][leg]['skor'] >= 0.5 for x in sel)}" for leg in LEGS)
        print(f"  {r:3d} Hz | {int(np.median([x['etkin'] for x in sel])):5d} | {cells}")
    return rows


def main_hybrid(workers: int):
    jobs = [("puruzsuz", 300.0), ("spike", 20.0), ("spike", 100.0), ("spike", 300.0), ("spike", 1000.0)]
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(hybrid_run, *zip(*jobs)))
    for r in rows:
        cells = ", ".join(f"{leg} {v['etkin']}/{v['skor']:.2f}/{v['en_yuksek_hz']:.0f}Hz" for leg, v in r["bacaklar"].items())
        print(f"  {r['mod']:8s} süzgeç {r['suzgec_ms']:6.0f} ms: DNg100 gerçek {r['dng100_gercek_hz']}; ağ etkin {r['etkin']:5d} | {cells}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=32)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--bacaklar", action="store_true")
    ap.add_argument("--hibrit", action="store_true")
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    if args.bacaklar or args.hibrit:
        rows = main_legs(args.workers) if args.bacaklar else main_hybrid(args.workers)
        name = "bacaklar" if args.bacaklar else "hibrit"
        path = RUNS / f"vnc-{name}-{time.strftime('%Y%m%d-%H%M%S')}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False))
        print(f"sonuçlar: {path}")
        return
    conditions = [("gercek", 0.1), ("sinaps", 0.1), ("gercek", 0.025)]
    out = {}
    t0 = time.time()
    with ProcessPoolExecutor(args.workers) as ex:
        for size_source, dt in conditions:
            n = args.replicates if dt == 0.1 else max(4, args.replicates // 4)
            rows = list(ex.map(simulate, range(n), [size_source] * n, [dt] * n))
            key = f"{size_source}_dt{dt}"
            out[key] = {"ozet": summarize(rows), "kosular": rows}
            print(key, json.dumps(out[key]["ozet"], ensure_ascii=False), f"({time.time() - t0:.0f} sn)", flush=True)
            for r in rows[:6]:
                print("   ", {k: v for k, v in r.items() if k != "iz"})
    path = RUNS / f"vnc-rhythm-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False))
    print(f"sonuçlar: {path}")


if __name__ == "__main__":
    main()
