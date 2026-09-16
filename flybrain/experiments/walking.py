"""Yürüme komut nöronu DNg100 uyarıldığında bacak ritmi oluşuyor mu?

Pugliese ve ark. (2025), sinir kordonu konnektomunun DNg100 uyarımıyla bacak motor
nöronlarında 7-15 Hz ritim ürettiğini gösterdi. Burada aynı uyarım proje beyin
ayarıyla (K-011) ve sinaptik depresyon muafiyetinin farklı kapsamlarıyla deneniyor.

Ölçülen her grup için: nöron başına hız, ateşleyen nöron sayısı ve nüfus spike
dizisinin 2-40 Hz bandındaki baskın frekansı (ilk 500 ms geçiş olarak atılır).

Kullanım:
    python -m flybrain.experiments.walking [--hz 50 150] [--duration 2000]
"""

import argparse
import time

import numpy as np

from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.sim import BRAIN_PARAMS, LIFParams, Simulator

CPG_TYPES = ["IN17A001", "INXXX466", "IN16B036"]  # Pugliese ve ark. 2025, E1 / E2 / I1
TRANSIENT_MS = 500.0
BIN_MS = 5.0


def groups(conn: Connectome) -> dict[str, np.ndarray]:
    n = conn.neurons
    t = n["type"].astype(str)
    sc = n.superclass.astype(str)
    return {
        "DNg100": np.flatnonzero(t == "DNg100"),
        "CPG": np.flatnonzero(t.isin(CPG_TYPES)),
        "bacak MN": np.flatnonzero((sc == "vnc_motor") & n.subclass.astype(str).isin(["fl", "ml", "hl"])),
    }


def exemptions(conn: Connectome, dng100: np.ndarray) -> dict[str, np.ndarray | None]:
    sc = conn.neurons.superclass.astype(str)
    dn = sc == "descending_neuron"
    return {
        "muafiyet yok": None,
        "DNg100 muaf": dng100,
        "inen nöronlar muaf": np.flatnonzero(dn),
        "inen + VNC muaf": np.flatnonzero(dn | sc.str.startswith("vnc")),
    }


def dominant_frequency(times_ms: np.ndarray, duration_ms: float) -> tuple[float, float]:
    """2-40 Hz bandındaki tepe frekansı ve o frekansın banttaki güç payı."""
    if len(times_ms) < 20:
        return 0.0, 0.0
    h, _ = np.histogram(times_ms, bins=np.arange(TRANSIENT_MS, duration_ms + BIN_MS, BIN_MS))
    p = np.abs(np.fft.rfft(h - h.mean())) ** 2
    f = np.fft.rfftfreq(len(h), BIN_MS / 1000)
    band = (f >= 2) & (f <= 40)
    k = np.argmax(np.where(band, p, 0))
    return float(f[k]), float(p[k] / p[band].sum())


def probe(conn: Connectome, params: LIFParams, exempt, hz: float, duration_ms: float, seed: int = 0):
    g = groups(conn)
    rec = np.concatenate(list(g.values()))
    sim = Simulator(conn, params, seed=seed, std_exempt=exempt)
    res = sim.run(duration_ms, g["DNg100"], hz, record=rec, max_records=5_000_000)
    t = res.spike_steps * params.dt_ms
    late = t >= TRANSIENT_MS
    sec = (duration_ms - TRANSIENT_MS) / 1000
    out = {}
    for name, idx in g.items():
        m = late & np.isin(res.spike_neurons, idx)
        f, share = dominant_frequency(t[m], duration_ms)
        out[name] = {
            "hz": m.sum() / len(idx) / sec,
            "aktif": len(np.unique(res.spike_neurons[m])),
            "n": len(idx),
            "tepe_hz": f,
            "guc_payi": share,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hz", type=float, nargs="+", default=[50.0, 150.0])
    ap.add_argument("--duration", type=float, default=2000.0)
    args = ap.parse_args()

    conn = load_connectome()
    g = groups(conn)
    print("| depresyon muafiyeti | DNg100 uyarımı | grup | Hz/nöron | aktif | tepe frekans (güç payı) |")
    print("|---|---|---|---|---|---|")
    for name, ex in exemptions(conn, g["DNg100"]).items():
        for hz in args.hz:
            t0 = time.time()
            res = probe(conn, BRAIN_PARAMS, ex, hz, args.duration)
            for grp, r in res.items():
                print(
                    f"| {name} | {hz:.0f} Hz | {grp} | {r['hz']:.1f} | {r['aktif']}/{r['n']} "
                    f"| {r['tepe_hz']:.1f} Hz ({r['guc_payi']:.2f}) |",
                    flush=True,
                )
            print(f"<!-- {name}, {hz:.0f} Hz: {time.time() - t0:.0f} sn -->", flush=True)


if __name__ == "__main__":
    main()
