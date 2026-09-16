"""Konnektomda görünmeyen, fizyolojik olarak ölçülmüş elektriksel sinapslar (K-023).

Elektron mikroskobu konnektomu kimyasal sinapsları gösterir; elektriksel sinapslar
(gap junction) görünmez. Bazı devrelerde asıl iletimi bunlar yapar. Burada yalnızca
literatürde ölçülmüş ve davranış için kritik olanlar eklenir.

Ağırlık, ölçülen iletimi (tek presinaptik spike → postsinaptik spike) sağlayacak
şekilde nöron modelinin kendi denkleminden hesaplanır: tek bir sinaptik olayın
membranda yarattığı tepe gerilim, eşik farkının GAP_MARGIN katı olur. Eşleşme,
konnektomdaki kimyasal sinapslarla aynı taraftadır (sol dev lif → sol TTMn).
"""

import numpy as np
import scipy.sparse as sp

from flybrain.connectome.connectome import Connectome
from flybrain.sim.lif import LIFParams

GAP_MARGIN = 2.0

# (presinaptik tip, postsinaptik tip, kaynak)
GAP_JUNCTIONS = [
    ("DNp01", "TTMn",
     "Dev lif → TTMn: karma elektriksel-kimyasal sinaps; tek dev lif spike'ı TTMn'de 1:1 spike "
     "(Tanouye ve Wyman 1980; Allen ve ark. 2006)"),
    ("DNp01", "PSI",
     "Dev lif → PSI: elektriksel sinaps, 1:1 iletim (Tanouye ve Wyman 1980; Allen ve ark. 2006)"),
]


def psp_peak_factor(p: LIFParams) -> float:
    """Tek sinaptik olayın (g += w) membranda yarattığı tepe gerilimin w'ye oranı."""
    tm, ts = p.tau_m_ms, p.tau_syn_ms
    t_peak = np.log(tm / ts) * tm * ts / (tm - ts)
    return ts / (tm - ts) * (np.exp(-t_peak / tm) - np.exp(-t_peak / ts))


def equivalent_synapses(p: LIFParams) -> int:
    """1:1 iletim için gereken, kimyasal sinaps sayısı cinsinden ağırlık."""
    need_mv = GAP_MARGIN * (p.v_thresh_mv - p.v_rest_mv)
    return int(np.ceil(need_mv / (psp_peak_factor(p) * p.w_syn_mv)))


def with_electrical(conn: Connectome, params: LIFParams) -> tuple[Connectome, np.ndarray, list[dict]]:
    """Elektriksel sinapsları eklenmiş yeni bir konnektom döndürür.

    Döndürür: (konnektom, depresyondan muaf tutulacak presinaptik nöronlar, eklenenlerin listesi).
    Elektriksel sinapslar vezikül tüketmediği için presinaptik nöronlar depresyondan muaftır.
    """
    t = conn.neurons["type"].fillna("").astype(str).to_numpy(dtype=object)
    side = conn.neurons.side.fillna("").astype(str).to_numpy(dtype=object)
    w = equivalent_synapses(params)
    rows, cols, added = [], [], []
    for pre_t, post_t, source in GAP_JUNCTIONS:
        for pre in np.flatnonzero(t == pre_t):
            for post in np.flatnonzero((t == post_t) & (side == side[pre])):
                rows.append(post)
                cols.append(pre)
                added.append({"pre": pre_t, "post": post_t, "side": side[pre], "esdeger_sinaps": w,
                              "kimyasal_sinaps": int(conn.W[post, pre]), "kaynak": source})
    delta = sp.csc_matrix((np.full(len(rows), w, dtype=conn.W.dtype), (rows, cols)), shape=conn.W.shape)
    W = (conn.W + delta).tocsc()
    W.sort_indices()
    exempt = np.unique(cols).astype(np.int64)
    return Connectome(conn.neurons, W, conn.label + "+gap"), exempt, added
