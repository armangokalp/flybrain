"""MaleCNS v1.0 nöron boyutları (voksel sayısı) — sinir kordonu hız modeli için (K-025).

Düz konnektom dosyalarında boyut yok; neuPrint girdi tablosunda (Neuprint_Neurons.feather,
4,6 GB) var. Dosyanın tamamı indirilmez: Arrow dosyası HTTP aralık istekleriyle açılır ve
yalnızca gövde kimliği ile boyut sütunları, izlenmiş nöronların bulunduğu ilk parçalardan
okunur (~5 MB). İlk 6 parça izlenmiş nöronların %98,8'ini içeriyor; kalanlar dosyaya
dağılmış durumda ve okunmuyor (`with_fallback` onlar için aynı tipin medyanını kullanır).

Kullanım:
    python -m flybrain.connectome.sizes [--batches 6]
"""

import argparse
import io
import urllib.request

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from flybrain.paths import RAW

URL = "https://storage.googleapis.com/flyem-male-cns/v1.0/database/neuprint-inputs/Neuprint_Neurons.feather"
SIZES = RAW / "neuron-sizes-male-cns-v1.0.parquet"
COLUMNS = {"bodyId:long": "bodyId", "size:long": "size"}


class HTTPRangeFile(io.RawIOBase):
    """Yalnızca istenen bayt aralıklarını indiren, salt okunur dosya nesnesi."""

    def __init__(self, url: str):
        self.url = url
        self.pos = 0
        self.fetched = 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")) as r:
            self.size = int(r.headers["Content-Length"])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        base = {0: 0, 1: self.pos, 2: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def readinto(self, b) -> int:
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req) as r:
            data = r.read()
        b[:len(data)] = data
        self.pos += len(data)
        self.fetched += len(data)
        return len(data)


def fetch(batches: int = 6) -> pd.DataFrame:
    f = HTTPRangeFile(URL)
    names = [x.name for x in ipc.open_file(pa.PythonFile(f, mode="r")).schema]
    keep = [names.index(c) for c in COLUMNS]
    reader = ipc.open_file(pa.PythonFile(f, mode="r"), options=ipc.IpcReadOptions(included_fields=keep))
    parts = [reader.get_batch(i).to_pandas() for i in range(min(batches, reader.num_record_batches))]
    df = pd.concat(parts, ignore_index=True).rename(columns=COLUMNS)
    df = df[df["size"].notna()].astype({"size": "int64"})
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SIZES)
    print(f"{len(df):,} gövde, {f.fetched / 1e6:.1f} MB okundu -> {SIZES}")
    return df


def load_sizes() -> pd.DataFrame:
    return pd.read_parquet(SIZES) if SIZES.exists() else fetch()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batches", type=int, default=6)
    fetch(ap.parse_args().batches)


if __name__ == "__main__":
    main()


def with_fallback(neurons: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Boyutu olmayan nöronlara aynı tipin, o da yoksa aynı süper sınıfın medyanını verir.

    Döndürür: (boyut, kaynak) — kaynak "olcum", "tip_medyani" ya da "sinif_medyani".
    """
    size = neurons["size"].astype(float)
    source = pd.Series(np.where(size.notna(), "olcum", ""), index=neurons.index, dtype=object)
    for key, label in (("type", "tip_medyani"), ("superclass", "sinif_medyani")):
        med = size.groupby(neurons[key]).transform("median")
        fill = size.isna() & med.notna()
        size[fill] = med[fill]
        source[fill] = label
    return size, source
