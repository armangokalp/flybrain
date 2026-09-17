"""Gövdeli sinek telefonda akışa bakar ve karar verir (K-016, K-020, K-030, K-032).

Bir posta bakma (gövdesiz sinekteki flybrain/fly.py ile aynı düzen):
  1. Ekran sonraki posta solarak geçer (K-030); postun açıklaması koku, bildirimler ödül
     nöronlarına verilir.
  2. Sinek 500 ms'lik pencerelerle bakar. Her pencerenin sonunda kas kanalları, posta
     bakmaya başlandığından beri biriken spike'lardan okunur; gövde ölçüleri o pencerenin
     kaydından alınır (body/confirm.py).
  3. Eylem seçici, eşiği aşan ve gövdesi görünür biçimde hareket eden kanallar arasından
     karar verir (gövde onayı, K-032). Karar yoksa sinek bakmaya devam eder; MAX_WINDOWS
     sonunda ilgisini kaybeder.

Beyin ve gövde postlar arasında sıfırlanmaz. Düşen sineği deneyci yeniden yerleştirir (K-031).
"""

from dataclasses import dataclass

import numpy as np

from flybrain.body.confirm import MEASURES, BodyMeter, visible
from flybrain.body.embodied import EmbodiedFly
from flybrain.body.phone import FeedPost
from flybrain.fly import Post
from flybrain.motor.readout import MotorReadout
from flybrain.motor.selector import (
    CALIBRATION_EMBODIED_PATH,
    MAX_WINDOWS,
    WINDOW_MS,
    ActionSelector,
    Calibration,
    Decision,
)
from flybrain.senses.olfaction import OlfactoryEncoder
from flybrain.senses.reward import RewardEncoder
from flybrain.sim import Stimulus


@dataclass
class Observation:
    """Karar vermeden bakılan bir post: [pencere, ...] dizileri."""

    rates: np.ndarray        # [pencere, kanal] birikimli hızlar
    turns: np.ndarray        # [pencere] baş çevirme yönü
    measures: np.ndarray     # [pencere, ölçü] body/confirm.MEASURES
    upright: np.ndarray      # [pencere] en düşük diklik
    repositions: np.ndarray  # [pencere] deneycinin yerleştirme sayısı


def _upright(quat: np.ndarray) -> float:
    w, x, y, z = quat
    return float(1 - 2 * (x * x + y * y))


class FeedViewer:
    def __init__(self, fly: EmbodiedFly, calibration: Calibration | None = None, homeostasis: bool = True):
        if fly.feed is None:
            raise ValueError("sahne yok: EmbodiedFly(scene=SceneConfig()) ile kurulmalı")
        self.fly = fly
        self.smell = OlfactoryEncoder(fly.conn)
        self.reward = RewardEncoder(fly.conn)
        self.readout = MotorReadout(fly.conn)
        self.meter = BodyMeter(fly.body.dofs)
        self.counts = np.zeros(fly.conn.n, dtype=np.int64)
        fly.spike_counter = self.counts
        self.selector = None
        self.posts = 0
        if calibration is not None or CALIBRATION_EMBODIED_PATH.exists():
            self.selector = ActionSelector(calibration or Calibration.load(CALIBRATION_EMBODIED_PATH), homeostasis)

    def stimulus(self, post: Post) -> Stimulus:
        return self.smell.encode(post.caption) + self.reward.encode(post.rewards, post.punishments)

    def _begin(self, post: Post) -> Stimulus:
        self.counts[:] = 0
        self.fly.next_post(FeedPost(post.image, caption=post.caption))
        self.posts += 1
        if self.fly.recorder is not None:
            self.fly.recorder.event("post", sira=self.posts, aciklama=post.caption,
                                    odul=post.rewards, ceza=post.punishments)
        return self.stimulus(post)

    def _window(self, stim: Stimulus, w: int):
        trace = self.fly.run(WINDOW_MS, stim, record_every_ms=5.0)
        a = trace.arrays()
        rates, turn = self.readout.rates(self.counts, (w + 1) * WINDOW_MS)
        up = min(_upright(q) for q in a["thorax_quat"])
        return rates, turn, self.meter.measure(a), up, len(trace.repositions)

    def observe(self, post: Post, windows: int = MAX_WINDOWS) -> Observation:
        """Karar vermeden bakar (kalibrasyon için)."""
        stim = self._begin(post)
        rows = [self._window(stim, w) for w in range(windows)]
        return Observation(*(np.array(col) for col in zip(*rows)))

    def look(self, post: Post) -> Decision:
        """Posta bakar ve bir eyleme karar verir."""
        if self.selector is None:
            raise RuntimeError("karar vermek için gövdeli kalibrasyon gerekli (experiments/embodied_calibrate.py)")
        stim = self._begin(post)
        placed = 0
        for w in range(MAX_WINDOWS):
            rates, turn, measures, _, n = self._window(stim, w)
            placed += n
            decision = self.selector.step(w, rates, turn, visible(measures))
            if decision is not None:
                decision.body = {k: round(float(v), 4) for k, v in zip(MEASURES, measures)}
                decision.body["yeniden_yerlestirme"] = placed
                if self.fly.recorder is not None:
                    self.fly.recorder.event("karar", sira=self.posts, eylem=decision.action, kanal=decision.channel,
                                            pencere=decision.window, sure_ms=decision.dwell_ms,
                                            gerekce=decision.reason, z=decision.z, govde=decision.body)
                self.selector.learn(decision)
                return decision
        raise AssertionError("seçici son pencerede her zaman karar verir")

