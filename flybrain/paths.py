"""Proje genelinde kullanılan dizinler."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
CACHE = DATA / "cache"
RUNS = ROOT / "runs"
