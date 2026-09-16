"""Sinek: beyin + duyular + motor okuma + eylem seçimi.

Bir posta bakma döngüsü:
  1. Kaydırma: SCROLL_GAP_MS boyunca gri ekran. Önceki postun izi söner.
  2. Görsel, caption ve (varsa) bildirimler duyu nöronlarına verilir.
  3. Beyin 500 ms'lik pencerelerle çalışır. Her pencerenin sonunda kas kanalları,
     posta bakmaya başlandığından beri biriken spike'lardan okunur; eylem seçici
     karar verene kadar ya da MAX_WINDOWS dolana kadar devam eder.

Beyin durumu postlar arasında sıfırlanmaz (bkz. docs/02-mimari.md).
"""

from dataclasses import dataclass

import numpy as np

from flybrain.connectome.connectome import Connectome, load_connectome
from flybrain.motor.readout import MotorReadout
from flybrain.motor.selector import (
    MAX_WINDOWS,
    SCROLL_GAP_MS,
    WINDOW_MS,
    ActionSelector,
    Calibration,
    Decision,
)
from flybrain.senses.olfaction import OlfactoryEncoder
from flybrain.senses.reward import RewardEncoder
from flybrain.senses.vision import VisionConfig, VisionEncoder
from flybrain.sim import BRAIN_PARAMS, Simulator, Stimulus

VISION = VisionConfig(mode="onoff", r_max_hz=250.0)  # K-012


@dataclass
class Post:
    image: np.ndarray       # RGB, [0, 1]
    caption: str = ""
    rewards: int = 0        # sineğin kendi postlarına gelen beğeni/yorum, yeni takipçi
    punishments: int = 0    # takipçi kaybı


class Fly:
    def __init__(
        self,
        conn: Connectome | None = None,
        seed: int = 0,
        calibration: Calibration | None = None,
        homeostasis: bool = True,
    ):
        self.conn = conn or load_connectome()
        self.vision = VisionEncoder(self.conn, VISION)
        self.smell = OlfactoryEncoder(self.conn)
        self.reward = RewardEncoder(self.conn)
        self.readout = MotorReadout(self.conn)
        self.brain = Simulator(self.conn, BRAIN_PARAMS, seed=seed, std_exempt=self.vision.input_neurons)
        self.selector = ActionSelector(calibration, homeostasis) if calibration else None

    def stimulus(self, post: Post) -> Stimulus:
        return (
            self.vision.encode(post.image)
            + self.smell.encode(post.caption)
            + self.reward.encode(post.rewards, post.punishments)
        )

    def observe(self, post: Post, windows: int = MAX_WINDOWS) -> tuple[np.ndarray, np.ndarray]:
        """Karar vermeden bakar: [pencere, kanal] birikimli hızlar ve baş çevirme yönleri."""
        self.brain.run(SCROLL_GAP_MS)
        stim = self.stimulus(post)
        counts = np.zeros(self.conn.n, dtype=np.int64)
        rates, turns = [], []
        for w in range(windows):
            counts += self.brain.run(WINDOW_MS, stim).counts
            x, turn = self.readout.rates(counts, (w + 1) * WINDOW_MS)
            rates.append(x)
            turns.append(turn)
        return np.array(rates), np.array(turns)

    def look(self, post: Post) -> Decision:
        """Posta bakar ve bir eyleme karar verir."""
        if self.selector is None:
            raise RuntimeError("karar vermek için kalibrasyon gerekli")
        self.brain.run(SCROLL_GAP_MS)
        stim = self.stimulus(post)
        counts = np.zeros(self.conn.n, dtype=np.int64)
        for w in range(MAX_WINDOWS):
            counts += self.brain.run(WINDOW_MS, stim).counts
            x, turn = self.readout.rates(counts, (w + 1) * WINDOW_MS)
            decision = self.selector.step(w, x, turn)
            if decision is not None:
                self.selector.learn(decision)
                return decision
        raise AssertionError("seçici son pencerede her zaman karar verir")
