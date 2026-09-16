"""Koku kodlayıcısı: metin → koku alıcı nöron (ORN) uyarımı.

Sinek okuyamaz; her kelimeyi bir "koku molekülü" olarak algılar (K-013).

- Kelime → glomerüller: kelime ve glomerül adı birlikte özetlenir (blake2b);
  en küçük özete sahip GLOMERULI_PER_WORD glomerül seçilir (rendezvous hashing).
  Eşleme sabittir, sürümden ve rastgelelikten bağımsızdır; aynı kelime her zaman
  aynı kokuyu verir. Anlamla hiçbir ilişkisi yoktur.
- Metin → karışım: bir glomerülün etkinliği, onu seçen kelime sayısıdır. Hız,
  reseptör doygunluğu gibi doyar: hız = R_MAX · a / (a + HALF_SAT).
  Tek kelime 150 Hz verir (Faz 2 deneyleriyle aynı yoğunluk).
"""

import hashlib
import re
import unicodedata

import numpy as np

from flybrain.anatomy import SENSORY, pools
from flybrain.connectome.connectome import Connectome
from flybrain.sim.stimulus import Stimulus

GLOMERULI_PER_WORD = 3
R_MAX_HZ = 200.0
HALF_SAT = 1.0 / 3.0
MAX_WORDS = 40

_TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Kelimeleri ve emojileri ayırır; noktalama ve # gibi işaretleri atar."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("\u0307", "")
    tokens = []
    for tok in _TOKEN.findall(text):
        if tok[0].isascii() and not tok[0].isalnum() and tok[0] != "_":
            continue  # ASCII noktalama
        if unicodedata.category(tok[0])[0] in "PMCZ":
            continue  # diğer noktalama, birleştirici işaretler, görünmez karakterler
        tokens.append(tok)
    return tokens


def _score(word: str, glomerulus: str) -> bytes:
    return hashlib.blake2b(
        f"{word}\x00{glomerulus}".encode(), digest_size=8, person=b"flybrain-koku"
    ).digest()


class OlfactoryEncoder:
    def __init__(self, conn: Connectome):
        orn = pools(conn, SENSORY)["ORN"]
        types = conn.neurons.type.to_numpy()[orn]
        self.glomeruli = sorted(set(types))
        self._neurons = {g: orn[types == g] for g in self.glomeruli}

    def odor(self, word: str) -> tuple[str, ...]:
        """Bir kelimenin glomerül kümesi (sıralı)."""
        ranked = sorted(self.glomeruli, key=lambda g: _score(word, g))
        return tuple(sorted(ranked[:GLOMERULI_PER_WORD]))

    def activation(self, words: list[str]) -> dict[str, int]:
        act: dict[str, int] = {}
        for w in words[:MAX_WORDS]:
            for g in self.odor(w):
                act[g] = act.get(g, 0) + 1
        return act

    def encode_words(self, words: list[str]) -> Stimulus:
        idx, hz = [], []
        for g, a in self.activation(words).items():
            n = self._neurons[g]
            idx.append(n)
            hz.append(np.full(len(n), R_MAX_HZ * a / (a + HALF_SAT)))
        if not idx:
            return Stimulus.empty()
        return Stimulus.of(np.concatenate(idx), np.concatenate(hz))

    def encode(self, text: str) -> Stimulus:
        return self.encode_words(tokenize(text))
