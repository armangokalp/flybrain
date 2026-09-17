"""Yorumun metni: duygu sinekten, kelimeler koklanarak (K-036).

Sinek dil bilmiyor. Kelimeler **feed'den** geliyor: gördüğü açıklamalardaki her kelime bir koku
(K-013). Yorum yazarken sinek adayları sırayla kokluyor ve en çok **yaklaştığı** kelimeyi
seçiyor. Koklama sineğin o anki beyin durumunda yapılıyor; korkmuşken yaklaştığı kelime ile
başka durumdaki farklı olabilir. Beyin kelimeler arasında sıfırlanmıyor (K-005).

  yaklaşma = ileri kanalı − (geri kanalı + çıkış kanalı)

Duygu (motor/mood.py) kelimeyi doğrudan seçmez; yorumun kaç kelime olacağını ve sonundaki
emojiyi belirler (MOOD_STYLE, insan tarafından yazılmış küçük tablo) ve karar günlüğüne yazılır.

Kelime kütüphanesi sineğin gördüğü açıklamalardan birikir. Aday sayısı MAX_CANDIDATES ile
sınırlı, çünkü her koklama simülasyon zamanı harcıyor (SNIFF_MS).
"""

from dataclasses import dataclass, field

import numpy as np

from flybrain.motor.mood import MOOD_STYLE, MOODS, MoodReadout
from flybrain.motor.readout import CHANNELS, MotorReadout
from flybrain.senses.olfaction import OlfactoryEncoder, tokenize

SNIFF_MS = 300.0        # bir kelimenin koklanma süresi
MAX_CANDIDATES = 12     # her yorumda koklanacak en fazla kelime
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
    mood: str
    words: list[str]
    scores: dict[str, float]     # her adayın son yaklaşma skoru
    mood_z: dict[str, float]


def _approach(rates: np.ndarray) -> float:
    r = dict(zip(CHANNELS, rates))
    return float(r["ileri"] - r["geri"] - r["cikis"])


class CommentWriter:
    """Koklayarak kelime seçer; duyguyu okur ve yorumu kurar."""

    def __init__(self, fly, readout: MotorReadout, mood: MoodReadout,
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
        """Posta bakarken biriken spike'lardan duyguyu okur, sonra kelimeleri koklayarak seçer.

        counts: posta bakılırken biriken spike sayıları (karar okumasının kullandığı dizi).
        """
        mood, z = self.read_mood(counts, duration_ms)
        self.library.add(caption)
        wanted = MOOD_STYLE[mood]["words"]
        adaylar = self.candidates(caption)
        secilen: list[str] = []
        scores: dict[str, float] = {}
        while adaylar and len(secilen) < wanted:
            for w in adaylar:
                scores[w] = self.sniff(w)
            best = max(adaylar, key=lambda w: scores[w])
            if scores[best] <= 0.0:
                break  # kaçınma baskın: yorum burada biter (K-005)
            secilen.append(best)
            adaylar.remove(best)
        text = " ".join(secilen)
        if text:
            text = f"{text} {MOOD_STYLE[mood]['emoji']}"
        return Comment(text=text, mood=mood, words=secilen, scores=scores, mood_z=z)

    def candidates(self, caption: str = "") -> list[str]:
        return self.library.candidates(caption)


def mood_report(z: dict[str, float]) -> str:
    return ", ".join(f"{m} {z[m]:+.2f}" for m in MOODS)
