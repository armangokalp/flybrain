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

Sinek bağlıysa (K-040, body/tether.py) "çıkış" kararı postu bitirmez: kaçış hareketi olur,
gövde gidemez, sinek aynı posta bakmaya devam eder. Bkz. `look(on_struggle=...)`.
"""

from collections.abc import Callable
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

# Bağlı sinekte (K-040) bir postta en fazla kaç bakış nöbeti. Kaçış girişimi nöbeti bitirir,
# sinek aynı posta bakmaya devam eder. Üst sınır dünya tarafında bir kural: oturum ilerlesin
# diye var, sineğin devresine dokunmuyor. Ölçümde çırpınma zaten 1-2 nöbette sönüyor.
MAX_BOUTS = 5


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
        self.tethered = fly.tether is not None  # kaçışın gövde onayı değişir (K-040)
        if calibration is not None or CALIBRATION_EMBODIED_PATH.exists():
            self.selector = ActionSelector(calibration or Calibration.load(CALIBRATION_EMBODIED_PATH), homeostasis)

    def stimulus(self, post: Post) -> Stimulus:
        return self.smell.encode(post.caption) + self.reward.encode(post.rewards, post.punishments)

    def _screen_item(self, post: Post):
        """Ekrana basılacak nesne. Yerel akışta post bloğu; gerçek Instagram'da tam ekran
        görüntüsü (insta/session.py bunu değiştirir)."""
        return FeedPost(post.image, caption=post.caption)

    def _begin(self, post: Post) -> Stimulus:
        self.counts[:] = 0
        self.fly.next_post(self._screen_item(post))
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

    def look(self, post: Post, on_struggle: Callable[[Decision, int], None] | None = None) -> Decision:
        """Posta bakar ve bir eyleme karar verir.

        `on_struggle` verilirse sinek **bağlıdır** (K-040): "çıkış" kararı postu bitirmez.
        Sinek kaçış hareketini yapar, gidemez ve aynı posta bakmaya devam eder — yeni bir
        bakış nöbeti başlar (birikim sıfırlanır, ekran değişmez). Tek çıkış yolu başka bir
        karar vermek. Nöbet sayısı MAX_BOUTS'u aşarsa post ilgi kaybıyla kapanır.

        Sınır: Kalibrasyon istatistikleri postun **geçişle** başlayan ilk nöbetinden çıkarıldı.
        Sonraki nöbetler geçişsiz başlar (ekran zaten yerinde), yani görme uyarımı daha
        düşüktür ve eşikleri aşmak zorlaşır. Çırpınan sinek bu yüzden çoğunlukla ilgi kaybına
        doğru gider (docs/09-govde.md 18).
        """
        if self.selector is None:
            raise RuntimeError("karar vermek için gövdeli kalibrasyon gerekli (experiments/embodied_calibrate.py)")
        stim = self._begin(post)
        placed = 0
        bouts = MAX_BOUTS if on_struggle is not None else 1
        for bout in range(bouts):
            if bout:
                self.counts[:] = 0  # yeni nöbet: kanıt birikimi baştan
            for w in range(MAX_WINDOWS):
                rates, turn, measures, _, n = self._window(stim, w)
                placed += n
                decision = self.selector.step(w, rates, turn, visible(measures, self.tethered))
                if decision is None:
                    continue
                decision.body = {k: round(float(v), 4) for k, v in zip(MEASURES, measures)}
                decision.body["yeniden_yerlestirme"] = placed
                decision.bout = bout
                if self.fly.recorder is not None:
                    self.fly.recorder.event("karar", sira=self.posts, eylem=decision.action, kanal=decision.channel,
                                            pencere=decision.window, sure_ms=decision.dwell_ms,
                                            gerekce=decision.reason, z=decision.z, govde=decision.body,
                                            nobet=bout)
                # Kararı sinek verdi; homeostaz bunu kaçış girişiminde de görmeli, yoksa
                # çıkış eşiği bütçesinden sapar.
                self.selector.learn(decision)
                if on_struggle is not None and decision.action == "cikis":
                    on_struggle(decision, bout)
                    break  # kaçamadı: aynı posta yeni bir nöbetle bakmaya devam
                return decision
        return Decision("ilgi_kaybi", None, MAX_WINDOWS - 1, MAX_WINDOWS * WINDOW_MS * bouts,
                        {}, f"kaçış döngüsü: {bouts} nöbet boyunca çıkıştan başka karar yok")

