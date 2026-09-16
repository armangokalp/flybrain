"""Simülasyona verilen duyusal girdi: hangi nöron, kaç Hz Poisson."""

from dataclasses import dataclass

import numpy as np

# Poisson olayı her seferinde spike ürettiği için hız, refrakter sınıra (1 / 2,2 ms) yakın tutulur.
MAX_HZ = 400.0
# Bunun altındaki hızlar (ör. kayan nokta artıkları) uyarım sayılmaz.
MIN_HZ = 1e-6


@dataclass(frozen=True)
class Stimulus:
    idx: np.ndarray  # sıralı ve benzersiz nöron indeksleri
    hz: np.ndarray

    @staticmethod
    def empty() -> "Stimulus":
        return Stimulus(np.zeros(0, dtype=np.int64), np.zeros(0))

    @staticmethod
    def of(idx, hz) -> "Stimulus":
        """Tekrarlanan indekslerin hızlarını toplar; MIN_HZ altındaki hızları atar."""
        idx = np.asarray(idx, dtype=np.int64).ravel()
        hz = np.broadcast_to(np.asarray(hz, dtype=np.float64), idx.shape)
        uniq, inv = np.unique(idx, return_inverse=True)
        total = np.zeros(len(uniq))
        np.add.at(total, inv, hz)
        total = np.minimum(total, MAX_HZ)
        keep = total > MIN_HZ
        return Stimulus(uniq[keep], total[keep])

    def __add__(self, other: "Stimulus") -> "Stimulus":
        return Stimulus.of(np.r_[self.idx, other.idx], np.r_[self.hz, other.hz])

    def __len__(self) -> int:
        return len(self.idx)

    def scaled(self, factor: float) -> "Stimulus":
        return Stimulus.of(self.idx, self.hz * factor)
