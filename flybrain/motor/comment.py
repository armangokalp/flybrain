"""Yorumun metni: kelimeler koklanarak seçilir (K-036, K-041 ile daraltıldı).

Sinek dil bilmiyor. Kelimeler **feed'den** geliyor: gördüğü açıklamalardaki her kelime bir koku
(K-013). Yorum yazarken sinek adayları sırayla kokluyor ve en çok **yaklaştığı** kelimeyi
seçiyor. Koklama sineğin o anki beyin durumunda yapılıyor. Beyin kelimeler arasında
sıfırlanmıyor (K-005).

  yaklaşma = ileri kanalı − (geri kanalı + çıkış kanalı)

Yorum, yaklaşma skoru sıfırın altına düşünce biter: **uzunluğu da sinek belirliyor**. Sinek
hiçbir kelimeye yaklaşmıyorsa yorum boş kalır ve hiçbir şey yazılmaz.

**Duygu bileşeni yok (K-041).** K-036 duygunun (motor/mood.py) kelime seçimini değiştirmesini,
yorumun uzunluğunu ve sonundaki emojiyi belirlemesini öngörüyordu. Ölçüm bunu düşürdü (Z-40):
duygu okuması tekrarlanmıyor ve kelime sıralamasını değiştirmiyor. Tekrarlanmayan bir okumadan
emoji seçmek gürültüyü duygu diye sunmak olurdu. Emoji ve uzunluk tablosu (MOOD_STYLE) insan
tarafından yazılmıştı; ikisi de kaldırıldı. `mood` verilirse okuma yalnızca **günlüğe** yazılır,
metni etkilemez.

Kelime kütüphanesi sineğin gördüğü açıklamalardan birikir. Aday sayısı MAX_CANDIDATES ile
sınırlı, çünkü her koklama simülasyon zamanı harcıyor (SNIFF_MS).
"""

from dataclasses import dataclass, field

import numpy as np

from flybrain.motor.mood import MOODS, MoodReadout
from flybrain.motor.readout import CHANNELS, MotorReadout
from flybrain.senses.olfaction import OlfactoryEncoder, tokenize

SNIFF_MS = 300.0        # bir kelimenin koklanma süresi
MAX_CANDIDATES = 12     # her yorumda koklanacak en fazla kelime
# Yorumun uzunluğunu sinek belirliyor (yaklaşma sıfırın altına düşünce biter); bu yalnızca
# üst sınır: her kelime SNIFF_MS simülasyon zamanı harcıyor.
MAX_WORDS = 4
MIN_WORD_LEN = 2
LIBRARY_LIMIT = 200     # kütüphanede tutulan en yeni kelime sayısı


@dataclass
class WordLibrary:
    """Sineğin feed'de karşılaştığı kelimeler (en yenisi sonda)."""

    words: list[str] = field(default_factory=list)

    def add(self, text: str) -> None:
        for w in tokenize(text):
            if len(w) < MIN_WORD_LEN:
                continue
            if w in self.words:
                self.words.remove(w)
            self.words.append(w)
        del self.words[:-LIBRARY_LIMIT]

    def candidates(self, current: str = "", limit: int = MAX_CANDIDATES) -> list[str]:
        """Bu postun kelimeleri önce, sonra kütüphanedeki en yeniler."""
        out: list[str] = []
        for w in tokenize(current):
            if len(w) >= MIN_WORD_LEN and w not in out:
                out.append(w)
        for w in reversed(self.words):
            if len(w) >= MIN_WORD_LEN and w not in out:
                out.append(w)
        return out[:limit]


@dataclass
class Comment:
    text: str
    mood: str                    # yalnızca günlük için; metni etkilemez (K-041)
    words: list[str]
    scores: dict[str, float]     # her adayın son yaklaşma skoru
    mood_z: dict[str, float]


def _approach(rates: np.ndarray) -> float:
    r = dict(zip(CHANNELS, rates))
    return float(r["ileri"] - r["geri"] - r["cikis"])


class CommentWriter:
    """Koklayarak kelime seçer ve yorumu kurar (duygu verilirse yalnızca günlüğe yazılır)."""

    def __init__(self, fly, readout: MotorReadout, mood: MoodReadout | None = None,
                 smell: OlfactoryEncoder | None = None, sniff_ms: float = SNIFF_MS):
        self.fly = fly
        self.readout = readout
        self.mood = mood
        self.smell = smell or OlfactoryEncoder(fly.conn)
        self.sniff_ms = sniff_ms
        self.library = WordLibrary()

    def sniff(self, word: str) -> float:
        """Kelimeyi koklatır ve yaklaşma skorunu döner. Beyin sıfırlanmaz."""
        counts = np.zeros(self.fly.conn.n, dtype=np.int64)
        previous, self.fly.spike_counter = self.fly.spike_counter, counts
        try:
            self.fly.run(self.sniff_ms, self.smell.encode_words([word]))
        finally:
            self.fly.spike_counter = previous
        rates, _ = self.readout.rates(counts, self.sniff_ms)
        return _approach(rates)

    def read_mood(self, counts: np.ndarray, duration_ms: float) -> tuple[str, dict[str, float]]:
        return self.mood.dominant(counts, duration_ms)

    def write(self, counts: np.ndarray, duration_ms: float, caption: str = "") -> Comment:
        """Kelimeleri koklayarak seçer; yaklaşma bitince yorum da biter.

        counts: posta bakılırken biriken spike sayıları (karar okumasının kullandığı dizi).
        Duygu okuması yalnızca günlüğe yazılır, metni etkilemez (K-041).
        """
        mood, z = self.read_mood(counts, duration_ms) if self.mood is not None else ("", {})
        self.library.add(caption)
        adaylar = self.candidates(caption)
        secilen: list[str] = []
        scores: dict[str, float] = {}
        while adaylar and len(secilen) < MAX_WORDS:
            for w in adaylar:
                scores[w] = self.sniff(w)
            best = max(adaylar, key=lambda w: scores[w])
            if scores[best] <= 0.0:
                break  # kaçınma baskın: yorum burada biter (K-005)
            secilen.append(best)
            adaylar.remove(best)
        return Comment(text=" ".join(secilen), mood=mood, words=secilen, scores=scores, mood_z=z)

    def candidates(self, caption: str = "") -> list[str]:
        return self.library.candidates(caption)


def mood_report(z: dict[str, float]) -> str:
    return ", ".join(f"{m} {z[m]:+.2f}" for m in MOODS)
