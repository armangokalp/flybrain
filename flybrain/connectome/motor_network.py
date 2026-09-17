"""Sinir kordonu hız modelinin ağı: motor nöronlar ve premotor nöronları (K-025).

Pugliese ve ark. (2025) ön bacak alt ağının seçim ölçütü, altı bacağın motor
nöronlarına uygulanır:
  1. bacak motor nöronları (alt sınıf fl, ml, hl),
  2. bunlara en az bir sinaps yapan tüm nöronlar (premotor),
  3. premotor nöronlara en az bir sinaps yapan inen nöronlar.
Nörotransmitter tahmini olmayan premotor nöronlar dışarıda kalır (yazarlarla aynı).
Bacak dışı motor nöronlar (ör. TTMn) premotor olsalar da LIF'te kalır; ağa sınır girdisi olarak bağlanır.
Ağırlıklar ayrıca en az 5 sinaps eşiğiyle önbellekten gelir.

Bu ölçüt yazarların MaleCNS ön bacak tablosunun 4.309 nöronunun tamamını yeniden üretiyor.

Kanat, halter, karın ve boyun motor nöronlarının ağları eklendiğinde (neredeyse bütün
kordon) hız modeli kendini sürdüren doygun bir duruma geçiyor; bu ağlar LIF'te kalır
(bkz. docs/09-govde.md 8).

Seçim ham ağırlık dosyasını okuduğu için sonuç önbelleğe yazılır.

Kullanım:
    python -m flybrain.connectome.motor_network
"""

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as pf

from flybrain.connectome.build import WEIGHTS
from flybrain.connectome.connectome import Connectome
from flybrain.paths import CACHE

NETWORK = CACHE / "motor-network-legs-malecns-v1.0.parquet"
LEG_SUBCLASSES = ("fl", "ml", "hl")


def _presynaptic(w: pa.Table, post_ids: np.ndarray) -> np.ndarray:
    e = w.filter(pc.is_in(w["body_post"], pa.array(post_ids)))
    return np.unique(e["body_pre"].to_numpy())


def build(conn: Connectome) -> pd.DataFrame:
    nn = conn.neurons
    ids = nn.bodyId.to_numpy()
    sup = nn.superclass.fillna("").astype(str).to_numpy(dtype=object)
    sub = nn.subclass.fillna("").astype(str).to_numpy(dtype=object)
    w = pf.read_table(WEIGHTS, memory_map=True, columns=["body_pre", "body_post"])
    motor = ids[(sup == "vnc_motor") & np.isin(sub, LEG_SUBCLASSES)]
    pre = np.setdiff1d(np.intersect1d(_presynaptic(w, motor), ids), motor)
    info = nn.set_index("bodyId").loc[pre]
    premotor = pre[(info.nt_source.to_numpy() != "default") & (info.superclass.to_numpy() != "vnc_motor")]
    upstream = np.intersect1d(_presynaptic(w, premotor), ids)
    dn = upstream[np.isin(upstream, ids[sup == "descending_neuron"])]
    roles = pd.concat([
        pd.DataFrame({"bodyId": motor, "rol": "motor"}),
        pd.DataFrame({"bodyId": premotor, "rol": "premotor"}),
        pd.DataFrame({"bodyId": np.setdiff1d(dn, premotor), "rol": "inen"}),
    ], ignore_index=True)
    roles.to_parquet(NETWORK)
    return roles


def load(conn: Connectome) -> pd.DataFrame:
    return pd.read_parquet(NETWORK) if NETWORK.exists() else build(conn)


def main() -> None:
    from flybrain.connectome.connectome import load_connectome

    conn = load_connectome()
    roles = build(conn)
    sup = conn.neurons.set_index("bodyId").superclass
    print(roles.assign(sinif=sup.loc[roles.bodyId].to_numpy()).groupby(["rol", "sinif"]).size().to_string())


if __name__ == "__main__":
    main()
