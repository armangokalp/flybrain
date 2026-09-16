"""Simülasyona hazır konnektomun yüklenmesi ve nöron seçimi."""

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import scipy.sparse as sp

from flybrain.connectome.build import build, cache_label
from flybrain.paths import CACHE


@dataclass
class Connectome:
    neurons: pd.DataFrame  # satır i = simülasyondaki nöron i
    W: sp.csc_matrix       # W[post, pre] = işaret × sinaps sayısı (int32)
    label: str

    @property
    def n(self) -> int:
        return len(self.neurons)

    def select(self, **criteria: Any) -> np.ndarray:
        """Tüm kriterlere uyan nöronların indekslerini döndürür.

        Her kriter bir sütun adıdır. Değer bir dizgeyse tam eşleşme, liste ya da
        kümeyse üyelik, derlenmiş bir düzenli ifadeyse baştan eşleşme aranır.
        """
        mask = np.ones(self.n, dtype=bool)
        for column, value in criteria.items():
            col = self.neurons[column]
            if isinstance(value, re.Pattern):
                mask &= col.fillna("").str.match(value).to_numpy()
            elif isinstance(value, (list, tuple, set, frozenset)):
                mask &= col.isin(value).to_numpy()
            else:
                mask &= (col == value).to_numpy()
        return np.flatnonzero(mask)

    def index_of(self, body_ids) -> np.ndarray:
        body_ids = np.asarray(body_ids)
        all_ids = self.neurons.bodyId.to_numpy()
        idx = np.searchsorted(all_ids, body_ids)
        idx = np.clip(idx, 0, len(all_ids) - 1)
        missing = all_ids[idx] != body_ids
        if missing.any():
            raise KeyError(f"konnektomda olmayan bodyId: {body_ids[missing][:5].tolist()}")
        return idx


def load_connectome(min_synapses: int = 5) -> Connectome:
    label = cache_label(min_synapses)
    neurons_path = CACHE / f"neurons-{label}.parquet"
    weights_path = CACHE / f"weights-{label}.npz"
    if not (neurons_path.exists() and weights_path.exists()):
        build(min_synapses)
    neurons = pd.read_parquet(neurons_path)
    W = sp.load_npz(weights_path).tocsc()
    return Connectome(neurons=neurons, W=W, label=label)
