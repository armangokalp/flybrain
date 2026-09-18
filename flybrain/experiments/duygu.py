"""Duygu havuzları neden sessiz? (Z-40'ın kök nedeni)

K-036 yorumun metnini duygu okumasına dayandırıyordu; ön koşul düştü çünkü havuzlar referans
postlarda neredeyse hiç ateşlemiyor (korku 0,000 Hz, ödül 0,000 Hz) ve baskın duygu
tekrarlanmıyor. Bu deney sebebini arıyor. Üç soru, üç ölçüm:

  1. **Havuz ateşleyebiliyor mu?** Havuzun kendi nöronlarına doğrudan Poisson girdi verilir.
     Ateşlemezse sorun havuzun tanımında ya da nöronların modeldeki dinamiğinde.
  2. **Doğru uyaranla ateşliyor mu?** Her duyguya kendi uyaranı verilir: ödüle gelen beğeni,
     cezaya takipçi kaybı, beslemeye şeker, korkuya acı/kaçış yolu. Ateşliyorsa havuz sağlam
     ve sorun postların o uyaranı hiç içermemesi — yani sessizlik **doğru** davranış olur.
  3. **Posta bakarken havuza ne kadar sürüş geliyor?** Havuzun presinaptik ortaklarının o anki
     ateşleme hızı × sinaptik ağırlık. Sıfıra yakınsa sessizlik yukarıdan geliyor demektir;
     soru havuzdan bir katman öteye taşınır.

Uyaranlar gövdesiz beyne veriliyor (`sim.Simulator`): görme kodlaması durağan, gövde yok. Amaç
duygu devresinin **sürülebilirliğini** ölçmek, gövdeli oturumu taklit etmek değil.

Kullanım:
    python -m flybrain.experiments.duygu [--ms 2000] [--seed 7]
"""

import argparse
import json
import time

import numpy as np

from flybrain.anatomy import SENSORY, pools
from flybrain.connectome.connectome import load_connectome
from flybrain.experiments.post import VISION
from flybrain.experiments.vision import natural_images
from flybrain.motor.mood import MOODS, mood_pools
from flybrain.paths import RUNS
from flybrain.senses.olfaction import OlfactoryEncoder
from flybrain.senses.reward import RewardEncoder
from flybrain.senses.vision import VisionEncoder
from flybrain.sim import BRAIN_PARAMS, Simulator, Stimulus

DIRECT_HZ = 150.0  # havuza doğrudan verilen Poisson girdisi (sondalarınkiyle aynı)


def _rate(counts: np.ndarray, idx: np.ndarray, ms: float) -> float:
    """Havuzun nöron başına ateşleme hızı (Hz)."""
    return float(counts[idx].sum()) / max(len(idx), 1) / (ms / 1000.0)


def probes(conn) -> dict[str, Stimulus]:
    """Her duygunun **kendi** uyaranı, artı gerçekçi bir post ve boş ekran."""
    S = pools(conn, SENSORY)
    vis = VisionEncoder(conn, VISION)
    olf = OlfactoryEncoder(conn)
    image = list(natural_images(1, seed=21).values())[0]
    return {
        "bos": Stimulus.empty(),
        "post": vis.encode(image) + olf.encode("sabah kahve deniz mutlu"),
        "seker": Stimulus.of(S["seker"], 150.0),
        "aci": Stimulus.of(S["aci"], 150.0),
        "odul_20_begeni": RewardEncoder(conn).encode(rewards=20),
        "ceza_20_kayip": RewardEncoder(conn).encode(punishments=20),
    }


def run(ms: float, seed: int) -> dict:
    conn = load_connectome()
    havuzlar = mood_pools(conn)
    vis = VisionEncoder(conn, VISION)
    sondalar = probes(conn)

    print(f"{'havuz':14} {'nöron':>6}")
    for m in MOODS:
        print(f"{m:14} {len(havuzlar[m]):6}")

    # 1 + 2: sondalara yanıt
    tablo = {}
    for ad, stim in sondalar.items():
        sim = Simulator(conn, BRAIN_PARAMS, seed=seed, std_exempt=vis.input_neurons)
        counts = sim.run(ms, stim).counts
        tablo[ad] = {m: _rate(counts, havuzlar[m], ms) for m in MOODS}
        print(f"  sonda {ad} bitti", flush=True)

    # 1: havuzu doğrudan sür (sağlamlık denetimi)
    dogrudan = {}
    for m in MOODS:
        sim = Simulator(conn, BRAIN_PARAMS, seed=seed, std_exempt=vis.input_neurons)
        counts = sim.run(ms, Stimulus.of(havuzlar[m], DIRECT_HZ)).counts
        dogrudan[m] = _rate(counts, havuzlar[m], ms)
        print(f"  doğrudan {m} bitti", flush=True)

    # 3: posta bakarken havuza gelen presinaptik sürüş
    sim = Simulator(conn, BRAIN_PARAMS, seed=seed, std_exempt=vis.input_neurons)
    counts = sim.run(ms, sondalar["post"]).counts
    rates = counts / (ms / 1000.0)
    surus = {}
    W = conn.W.tocsr()  # W[post, pre]: havuzun satırları presinaptik ortakları verir
    for m in MOODS:
        alt = W[havuzlar[m]].tocoo()
        pre, w = alt.col, alt.data
        surus[m] = {"ortak": int(len(np.unique(pre))),
                    "aktif_ortak": int((rates[np.unique(pre)] > 0.5).sum()),
                    "surus_hz_agirlik": float((rates[pre] * w).sum() / max(len(havuzlar[m]), 1))}
    return {"sondalar": tablo, "dogrudan": dogrudan, "surus": surus,
            "havuz_boyu": {m: int(len(havuzlar[m])) for m in MOODS}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ms", type=float, default=2000.0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    r = run(args.ms, args.seed)

    print(f"\nhavuzların uyaranlara yanıtı (nöron başına Hz, {args.ms:.0f} ms)")
    print(f"{'sonda':16} " + " ".join(f"{m:>12}" for m in MOODS))
    for ad, satir in r["sondalar"].items():
        print(f"{ad:16} " + " ".join(f"{satir[m]:12.3f}" for m in MOODS))
    print(f"{'DOĞRUDAN SÜRÜŞ':16} " + " ".join(f"{r['dogrudan'][m]:12.3f}" for m in MOODS))

    print("\nposta bakarken havuza gelen sürüş")
    print(f"{'duygu':14} {'ortak':>8} {'aktif ortak':>12} {'sürüş (Hz×ağırlık/nöron)':>26}")
    for m in MOODS:
        s = r["surus"][m]
        print(f"{m:14} {s['ortak']:8} {s['aktif_ortak']:12} {s['surus_hz_agirlik']:26.1f}")

    out = RUNS / f"duygu-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print(f"\nkayıt: {out}")


if __name__ == "__main__":
    main()
