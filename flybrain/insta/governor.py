"""Güvenlik valisi: eylemleri yalnızca **engeller**, asla seçmez (K-007).

Üç işi var:
  1. **Hız sınırları (Z-10):** Saatlik ve günlük üst sınırlar, eylemler arası en az bekleme.
     Sayaçlar oturumlar arasında dosyada tutulur; gün sınırı son 24 saati kapsar.
  2. **İçerik vetosu (Z-13):** Yorumda yasaklı kelime varsa eylem engellenir; sinek bir sonraki
     tercihine geçer. Liste `yasakli.txt`; kullanıcı genişletebilir.
  3. **Doğrulama algılama (Z-11):** Instagram doğrulama isterse ya da oturum düşerse durur ve
     bildirir. Sistem doğrulamayı **atlatmaya çalışmaz**; kullanıcı elle çözer.

Vali bir eylemi engellediğinde bunun gerekçesi karar günlüğüne yazılır; sineğin kararı
değişmez, yalnızca uygulanmaz.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from flybrain.paths import RUNS

ACTIONS = ("begen", "kaydet", "takip", "yorum", "paylas", "story")
LOG = RUNS / "insta" / "eylemler.jsonl"
BANNED = Path(__file__).with_name("yasakli.txt")
# Instagram'ın doğrulama ve kısıtlama sayfaları (Z-11).
CHALLENGE_URLS = ("/challenge/", "/accounts/suspended", "/accounts/disabled", "/accounts/login")


@dataclass(frozen=True)
class Limits:
    """Isınma ayarı: gerçek hesapta ilk oturumlar için bilinçli olarak düşük (Z-10)."""

    hourly: dict[str, int] = field(default_factory=lambda: {
        "begen": 20, "kaydet": 10, "takip": 3, "yorum": 2, "paylas": 1, "story": 2})
    daily: dict[str, int] = field(default_factory=lambda: {
        "begen": 100, "kaydet": 50, "takip": 10, "yorum": 8, "paylas": 2, "story": 4})
    gap_s: float = 20.0          # aynı türden iki eylem arasında en az bekleme
    any_gap_s: float = 5.0       # herhangi iki eylem arasında en az bekleme

    @classmethod
    def only(cls, actions, base: "Limits | None" = None) -> "Limits":
        """Yalnızca verilen eylemlere izin veren sınırlar; ötekiler 0 (kullanıcı kararı).

        Sineğin kararı değişmez; izin verilmeyen eylem uygulanmaz ve gerekçesi kayda geçer.
        """
        base = base or cls()
        izin = set(actions)
        bilinmeyen = izin - set(ACTIONS)
        if bilinmeyen:
            raise ValueError(f"bilinmeyen eylem: {sorted(bilinmeyen)}")
        return cls(hourly={a: (base.hourly[a] if a in izin else 0) for a in ACTIONS},
                   daily={a: (base.daily[a] if a in izin else 0) for a in ACTIONS},
                   gap_s=base.gap_s, any_gap_s=base.any_gap_s)


class Vetoed(Exception):
    """Vali eylemi engelledi."""


class Stopped(Exception):
    """Oturum durduruldu: doğrulama ya da kısıtlama (Z-11)."""


def banned_words() -> set[str]:
    if not BANNED.exists():
        return set()
    out = set()
    for line in BANNED.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip().lower()
        if line:
            out.add(line)
    return out


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^\wçğıöşüÇĞİÖŞÜ]+", text.lower()) if w]


class Governor:
    def __init__(self, limits: Limits | None = None, log: Path | str = LOG, dry_run: bool = True):
        """dry_run: eylemler tıklanmaz, yalnızca kaydedilir (Faz 8'in ilk kipi)."""
        self.limits = limits or Limits()
        self.log = Path(log)
        self.dry_run = dry_run
        self.banned = banned_words()
        self.history: list[dict] = []
        if self.log.exists():
            self.history = [json.loads(line) for line in self.log.read_text().splitlines() if line.strip()]

    def _count(self, action: str, window_s: float, now: float) -> int:
        return sum(1 for e in self.history if e["eylem"] == action and now - e["t"] < window_s and e["uygulandi"])

    def _last(self, action: str | None, now: float) -> float:
        times = [e["t"] for e in self.history if e["uygulandi"] and (action is None or e["eylem"] == action)]
        return now - max(times) if times else float("inf")

    def check(self, action: str, text: str = "", now: float | None = None) -> None:
        """Eylem uygulanabilir mi; uygulanamazsa `Vetoed` fırlatır."""
        now = time.time() if now is None else now
        if action not in ACTIONS:
            raise ValueError(f"bilinmeyen eylem: {action}")
        if text:
            hit = sorted(set(_words(text)) & self.banned)
            if hit:
                raise Vetoed(f"yasaklı kelime: {', '.join(hit)}")
        h, d = self.limits.hourly[action], self.limits.daily[action]
        if h == 0 or d == 0:
            raise Vetoed("bu eylem kapalı (kullanıcı izni yok)")
        if self._count(action, 3600, now) >= h:
            raise Vetoed(f"saatlik sınır ({h})")
        if self._count(action, 86400, now) >= d:
            raise Vetoed(f"günlük sınır ({d})")
        gap = self._last(action, now)
        if gap < self.limits.gap_s:
            raise Vetoed(f"aynı eylemden {gap:.0f} sn önce yapıldı (en az {self.limits.gap_s:.0f} sn)")
        gap = self._last(None, now)
        if gap < self.limits.any_gap_s:
            raise Vetoed(f"önceki eylemden {gap:.0f} sn geçti (en az {self.limits.any_gap_s:.0f} sn)")

    def record(self, action: str, applied: bool, note: str = "", now: float | None = None) -> dict:
        """Eylemi geçmişe ve dosyaya yazar (engellenenler de yazılır)."""
        entry = {"t": time.time() if now is None else now, "eylem": action, "uygulandi": bool(applied), "not": note}
        self.history.append(entry)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def watch(self, url: str, logged_in: bool = True) -> None:
        """Sayfa doğrulama ya da kısıtlama sayfasına düştüyse oturumu durdurur (Z-11)."""
        for mark in CHALLENGE_URLS:
            if mark in url:
                raise Stopped(f"Instagram doğrulama ya da kısıtlama sayfası açıldı: {url}")
        if not logged_in:
            raise Stopped("oturum düştü: tarayıcıda elle giriş yapılmalı")

    def remaining(self, now: float | None = None) -> dict[str, tuple[int, int]]:
        """Her eylem için (saatlik kalan, günlük kalan)."""
        now = time.time() if now is None else now
        return {a: (self.limits.hourly[a] - self._count(a, 3600, now),
                    self.limits.daily[a] - self._count(a, 86400, now)) for a in ACTIONS}


def report(gov: Governor) -> str:
    rows = [f"{a}: saatlik {h}, günlük {d}" for a, (h, d) in gov.remaining().items()]
    kip = "kuru çalıştırma" if gov.dry_run else "gerçek eylemler"
    return f"[{kip}] kalan — " + "; ".join(rows)
