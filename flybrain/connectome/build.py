"""Ham MaleCNS dosyalarından simülasyona hazır önbellek üretir.

Çıktılar (data/cache/):
    neurons-<etiket>.parquet   nöron tablosu; satır sırası = simülasyondaki indeks
    weights-<etiket>.npz       CSC seyrek matris, W[post, pre] = işaret × sinaps sayısı

Kullanım:
    python -m flybrain.connectome.build [--min-synapses 5]
"""

import argparse
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as pf
import scipy.sparse as sp

from flybrain.paths import CACHE, RAW

ANNOTATIONS = RAW / "body-annotations-male-cns-v1.0-minconf-0.5.feather"
TRANSMITTERS = RAW / "body-neurotransmitters-male-cns-v1.0.feather"
WEIGHTS = RAW / "connectome-weights-male-cns-v1.0-minconf-0.5.feather"

# Shiu ve ark. (2024): asetilkolin uyarıcı, GABA ve glutamat ketleyici.
# Histamin fotoreseptörlerin vericisidir ve klor kanalı açar, bu yüzden ketleyici.
# Modülatörler (dopamin, serotonin, oktopamin) varsayım olarak uyarıcı alınır (bkz. K-008).
SIGN = {
    "acetylcholine": 1,
    "glutamate": -1,
    "gaba": -1,
    "histamine": -1,
    "dopamine": 1,
    "serotonin": 1,
    "octopamine": 1,
}
DEFAULT_SIGN = 1  # vericisi belirsiz nöronlar; kolinerjik çoğunluk varsayımı

KEEP_COLUMNS = [
    "bodyId", "type", "instance", "superclass", "class", "subclass",
    "somaSide", "rootSide", "fruDsx", "flywireType", "synonyms",
    "assignedOlHex1", "assignedOlHex2", "somaLocation", "entryNerve",
]


def cache_label(min_synapses: int) -> str:
    return f"malecns-v1.0-w{min_synapses}"


def _neuron_table() -> pd.DataFrame:
    a = pd.read_feather(ANNOTATIONS)
    a = a[a.status == "Traced"][KEEP_COLUMNS]
    a = a.sort_values("bodyId", ignore_index=True)

    # Duyu nöronlarının somasi beyin dışında olduğundan tarafları kökten gelir.
    a["side"] = a.somaSide.where(a.somaSide.isin(["L", "R"]), a.rootSide)
    a = a.drop(columns=["somaSide", "rootSide"])

    a = a.rename(columns={"assignedOlHex1": "hex1", "assignedOlHex2": "hex2"})

    # Soma konumu 8 nm'lik voksel biriminde [x, y, z] listesi olarak gelir.
    soma = np.full((len(a), 3), np.nan)
    has = a.somaLocation.notna().to_numpy()
    soma[has] = np.stack(a.somaLocation[has].to_numpy())
    a[["soma_x", "soma_y", "soma_z"]] = soma
    a = a.drop(columns=["somaLocation"])

    nt = pd.read_feather(TRANSMITTERS, columns=["body", "consensus_nt", "predicted_nt"])
    a = a.merge(nt, left_on="bodyId", right_on="body", how="left").drop(columns=["body"])
    consensus_ok = a.consensus_nt.isin(SIGN.keys())
    predicted_ok = a.predicted_nt.isin(SIGN.keys())
    a["nt"] = a.consensus_nt.where(consensus_ok, a.predicted_nt.where(predicted_ok))
    a["nt_source"] = np.select(
        [consensus_ok, predicted_ok], ["consensus", "predicted"], default="default"
    )
    a["sign"] = a.nt.map(SIGN).fillna(DEFAULT_SIGN).astype(np.int8)
    return a.drop(columns=["consensus_nt", "predicted_nt"])


def _weight_matrix(body_ids: np.ndarray, signs: np.ndarray, min_synapses: int) -> sp.csc_matrix:
    w = pf.read_table(WEIGHTS, memory_map=True)
    w = w.filter(pc.greater_equal(w["weight"], min_synapses))
    ids = pa.array(body_ids)
    w = w.filter(
        pc.and_(
            pc.and_(pc.is_in(w["body_pre"], ids), pc.is_in(w["body_post"], ids)),
            pc.not_equal(w["body_pre"], w["body_post"]),
        )
    )
    pre = np.searchsorted(body_ids, w["body_pre"].to_numpy())
    post = np.searchsorted(body_ids, w["body_post"].to_numpy())
    count = w["weight"].to_numpy().astype(np.int32)
    n = len(body_ids)
    W = sp.csc_matrix((count * signs[pre], (post, pre)), shape=(n, n), dtype=np.int32)
    W.sum_duplicates()
    return W


def build(min_synapses: int = 5) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    label = cache_label(min_synapses)

    t0 = time.time()
    neurons = _neuron_table()
    body_ids = neurons.bodyId.to_numpy()
    W = _weight_matrix(body_ids, neurons.sign.to_numpy().astype(np.int32), min_synapses)

    neurons.to_parquet(CACHE / f"neurons-{label}.parquet")
    sp.save_npz(CACHE / f"weights-{label}.npz", W, compressed=False)
    print(
        f"{label}: {len(neurons):,} nöron, {W.nnz:,} bağlantı, "
        f"{np.abs(W.data).sum():,} sinaps ({time.time() - t0:.1f} sn)"
    )
    return label


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--min-synapses", type=int, default=5)
    args = parser.parse_args()
    build(args.min_synapses)


if __name__ == "__main__":
    main()
