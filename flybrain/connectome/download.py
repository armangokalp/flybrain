"""MaleCNS v1.0 düz konnektom dosyalarını indirir.

Yalnızca standart kütüphane kullanır. Yarım kalan indirmeler kaldığı yerden
devam eder, her dosya sunucunun bildirdiği MD5 özetiyle doğrulanır.

Kullanım:
    python -m flybrain.connectome.download
"""

import base64
import hashlib
import sys
import urllib.request
from pathlib import Path

from flybrain.paths import RAW

BASE_URL = (
    "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
)

# dosya adı -> (bayt, base64 MD5); değerler sunucunun HEAD yanıtından alındı.
FILES = {
    "body-annotations-male-cns-v1.0-minconf-0.5.feather": (
        14_483_314,
        "UKdxh3DFciDxYLpPQxq4ng==",
    ),
    "body-neurotransmitters-male-cns-v1.0.feather": (
        43_282_834,
        "PYQrEv5cSe763lKNfdJKHw==",
    ),
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather": (
        1_051_241_946,
        "8w6dzKJc/QIb8eez2XVZng==",
    ),
}

CHUNK = 1 << 20


def _md5_b64(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return base64.b64encode(h.digest()).decode()


def fetch(name: str, size: int, md5: str, dest_dir: Path = RAW) -> Path:
    dest = dest_dir / name
    if dest.exists() and dest.stat().st_size == size:
        print(f"[var] {name}")
        return dest

    dest_dir.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    offset = part.stat().st_size if part.exists() else 0

    req = urllib.request.Request(BASE_URL + name)
    if offset:
        req.add_header("Range", f"bytes={offset}-")
    with urllib.request.urlopen(req) as resp, part.open("ab" if offset else "wb") as out:
        if offset and resp.status != 206:
            # Sunucu devam etmeyi desteklemedi; baştan yaz.
            out.seek(0)
            out.truncate()
            offset = 0
        done = offset
        next_report = done + 50 * CHUNK
        while block := resp.read(CHUNK):
            out.write(block)
            done += len(block)
            if done >= next_report:
                print(f"  {name}: {done / size:6.1%} ({done >> 20} / {size >> 20} MB)", flush=True)
                next_report += 50 * CHUNK

    if part.stat().st_size != size:
        raise RuntimeError(f"{name}: boyut uyuşmuyor ({part.stat().st_size} != {size})")
    if _md5_b64(part) != md5:
        part.unlink()
        raise RuntimeError(f"{name}: MD5 uyuşmuyor, dosya silindi; tekrar deneyin")
    part.rename(dest)
    print(f"[indirildi] {name}")
    return dest


def main() -> int:
    for name, (size, md5) in FILES.items():
        fetch(name, size, md5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
