"""Pekiştirme kodlayıcısı: Instagram bildirimleri → dopamin nöronları.

- Ödül (PAM): sineğin kendi postlarına gelen beğeni ve yorumlar, yeni takipçiler
- Ceza (PPL1): takipçi kaybı

Hız, olay sayısıyla doyarak artar: hız = R_MAX · n / (n + HALF_SAT).
Öğrenme kuralı Faz 8'de eklenecek; o zamana kadar bu sinyal yalnızca anlık
beyin aktivitesini etkiler.
"""

import numpy as np

from flybrain.anatomy import SENSORY, pools
from flybrain.connectome.connectome import Connectome
from flybrain.sim.stimulus import Stimulus

R_MAX_HZ = 150.0
HALF_SAT = 5.0


def _rate(n: int) -> float:
    return R_MAX_HZ * n / (n + HALF_SAT) if n > 0 else 0.0


class RewardEncoder:
    def __init__(self, conn: Connectome):
        p = pools(conn, SENSORY)
        self.pam = p["PAM"]
        self.ppl1 = p["PPL1"]

    def encode(self, rewards: int = 0, punishments: int = 0) -> Stimulus:
        return Stimulus.of(
            np.r_[self.pam, self.ppl1],
            np.r_[np.full(len(self.pam), _rate(rewards)), np.full(len(self.ppl1), _rate(punishments))],
        )
