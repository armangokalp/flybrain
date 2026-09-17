"""Bileşik göz geometrisi.

MaleCNS anotasyonları 15 kolon nöron tipi için altıgen kolon koordinatı
(`hex1`, `hex2`) veriyor. Bu modül:

1. Izgarayı düzleştirir. Fiziksel olarak en yakın komşular (±1,0), (0,±1),
   ±(1,1) adımlarıdır; bu, eksenleri arasında 120° olan bir altıgen ızgaradır:
   x = hex1 − hex2/2, y = hex2·√3/2.
2. Kolonların bakış yönlerini çıkarır. Lamina hücre gövdelerine küre oturtulur;
   her kolonun bakış yönü, kürenin o noktadaki dış normalidir. Yönler beyin
   eksenlerine göre ifade edilir: koku lobu PN'leri önde, Kenyon hücreleri arkada
   ve üstte, SEZ motor nöronları altta. Izgara → (φ, θ) doğrusal eşlemesi sağ
   gözden kurulur ve iki göze de uygulanır; iki göz aynı ayna simetrik
   koordinatları kullanıyor (üst kenar fotoreseptörleri her iki gözde aynı
   kolonlarda) ve sol gözün hücre gövdesi verisi eksik. Doğrulama: üst kenar
   (dorsal rim) kolonları yaklaşık +57° yükseklikte çıkıyor.
3. Koordinatı olmayan nöronların (fotoreseptörler, Tm3, sol L3...) kolonunu,
   koordinatlı partnerleriyle sinaps ağırlıklı oylamayla bulur.
4. Panoramik gösterim (K-014): post görseli sineğin tüm görme alanına yayılır.
   Görselin sol yarısı sol göze, sağ yarısı sağ göze düşer; görselin ortası
   tam önü, kenarları gözlerin en arka kolonlarını gösterir; üst kenar sırt yönüdür.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from flybrain.connectome.connectome import Connectome

LAMINA_TYPES = ["L1", "L2", "L3", "L5"]


def lattice_xy(hex1, hex2) -> np.ndarray:
    hex1 = np.asarray(hex1, dtype=float)
    hex2 = np.asarray(hex2, dtype=float)
    return np.c_[hex1 - hex2 / 2.0, hex2 * np.sqrt(3.0) / 2.0]


def _soma_mean(nn: pd.DataFrame, mask) -> np.ndarray:
    s = nn[mask & nn.soma_x.notna()]
    return s[["soma_x", "soma_y", "soma_z"]].to_numpy().mean(axis=0)


def body_axes(conn: Connectome) -> tuple[np.ndarray, np.ndarray, float]:
    """(ön birim vektörü, sırt birim vektörü, orta hattın x koordinatı)."""
    nn = conn.neurons
    pn = _soma_mean(nn, nn.type.fillna("").str.contains("adPN"))
    kc = _soma_mean(nn, nn["class"].eq("Kenyon_Cell"))
    mn = _soma_mean(nn, nn.superclass.eq("cb_motor"))
    anterior = pn - kc
    anterior /= np.linalg.norm(anterior)
    dorsal = kc - mn
    dorsal -= dorsal.dot(anterior) * anterior
    dorsal /= np.linalg.norm(dorsal)
    midline_x = _soma_mean(nn, nn.superclass.fillna("").str.startswith("cb_"))[0]
    return anterior, dorsal, midline_x


@dataclass(frozen=True)
class ViewMapping:
    """Izgara (x, y) → bakış yönü: φ (0° yan, +90° ön) ve θ (+ sırt), derece."""

    phi_coef: np.ndarray    # [ax, ay, sabit]
    theta_coef: np.ndarray
    phi_r2: float
    theta_r2: float

    def __call__(self, hex1, hex2) -> tuple[np.ndarray, np.ndarray]:
        X = np.c_[lattice_xy(hex1, hex2), np.ones(np.size(hex1))]
        return X @ self.phi_coef, X @ self.theta_coef


def fit_view_mapping(conn: Connectome, side: str = "R") -> ViewMapping:
    nn = conn.neurons
    anterior, dorsal, midline_x = body_axes(conn)
    s = nn[nn.type.isin(LAMINA_TYPES) & (nn.side == side) & nn.hex1.notna() & nn.soma_x.notna()]
    P = s[["soma_x", "soma_y", "soma_z"]].to_numpy()

    # Küre: |p|² = 2c·p + (r² − |c|²)
    sol, *_ = np.linalg.lstsq(np.c_[2 * P, np.ones(len(P))], (P**2).sum(axis=1), rcond=None)
    center = sol[:3]

    lateral = np.array([1.0 if P[:, 0].mean() > midline_x else -1.0, 0.0, 0.0])
    lateral -= lateral.dot(anterior) * anterior + lateral.dot(dorsal) * dorsal
    lateral /= np.linalg.norm(lateral)

    U = (P - center) / np.linalg.norm(P - center, axis=1, keepdims=True)
    phi = np.degrees(np.arctan2(U @ anterior, U @ lateral))
    theta = np.degrees(np.arcsin(np.clip(U @ dorsal, -1.0, 1.0)))

    X = np.c_[lattice_xy(s.hex1, s.hex2), np.ones(len(s))]
    cp, *_ = np.linalg.lstsq(X, phi, rcond=None)
    ct, *_ = np.linalg.lstsq(X, theta, rcond=None)

    def r2(y, yhat):
        return float(1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum())

    return ViewMapping(cp, ct, r2(phi, X @ cp), r2(theta, X @ ct))


def infer_columns(
    conn: Connectome, idx: np.ndarray, known: dict[int, tuple[float, float]] | None = None
) -> pd.DataFrame:
    """Koordinatı olmayan nöronlar için partner oylamasıyla (hex1, hex2).

    Hem çıkış hem giriş partnerleri, sinaps sayısıyla ağırlıklandırılarak
    kullanılır. Yalnızca aynı taraftaki koordinatlı partnerler sayılır.
    `known`, daha önce çıkarılmış kolonları da oylamaya katar (ör. R7 için R8).
    """
    nn = conn.neurons
    h1 = nn.hex1.to_numpy().astype(float)
    h2 = nn.hex2.to_numpy().astype(float)
    for n, (a, b) in (known or {}).items():
        h1[n], h2[n] = a, b
    side = nn.side.to_numpy()
    hexed = ~np.isnan(h1)
    W_out = abs(conn.W)                # sütun = pre
    W_in = W_out.tocsr()               # satır = post
    rows = []
    for n in np.asarray(idx):
        partners = np.r_[
            W_out.indices[W_out.indptr[n]:W_out.indptr[n + 1]],
            W_in.indices[W_in.indptr[n]:W_in.indptr[n + 1]],
        ]
        weights = np.r_[
            W_out.data[W_out.indptr[n]:W_out.indptr[n + 1]],
            W_in.data[W_in.indptr[n]:W_in.indptr[n + 1]],
        ]
        m = hexed[partners] & (side[partners] == side[n])
        if not m.any():
            continue
        votes = pd.Series(weights[m]).groupby([h1[partners[m]], h2[partners[m]]]).sum()
        (b1, b2) = votes.idxmax()
        rows.append((n, b1, b2, votes.max() / votes.sum()))
    return pd.DataFrame(rows, columns=["idx", "hex1", "hex2", "vote_share"])


class Eye:
    def __init__(self, conn: Connectome, view: ViewMapping | None = None):
        self.conn = conn
        self.view = view or fit_view_mapping(conn, "R")
        nn = conn.neurons
        cols = nn[nn.type.isin(LAMINA_TYPES + ["Mi1", "Tm1"]) & nn.hex1.notna()]
        phi, theta = self.view(cols.hex1, cols.hex2)
        self.phi_range = (float(phi.min()), float(phi.max()))
        self.theta_range = (float(theta.min()), float(theta.max()))
        self._inferred: dict[int, tuple[float, float]] = {}

    def uv(self, side: np.ndarray, hex1, hex2) -> tuple[np.ndarray, np.ndarray]:
        """Panoramik görsel koordinatları: u (0 sol, 1 sağ), v (0 üst, 1 alt)."""
        phi, theta = self.view(hex1, hex2)
        p0, p1 = self.phi_range
        t0, t1 = self.theta_range
        back = np.clip((p1 - phi) / (p1 - p0), 0.0, 1.0)  # 0 tam ön, 1 en arka
        u = np.where(np.asarray(side) == "R", 0.5 + 0.5 * back, 0.5 - 0.5 * back)
        v = np.clip((t1 - theta) / (t1 - t0), 0.0, 1.0)
        return u, v

    def neuron_uv(self, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Nöronların görsel koordinatları; kolonu bulunamayanlar düşürülür.

        Döndürür: (idx, u, v).
        """
        idx, side, h1, h2 = self.neuron_columns(idx)
        u, v = self.uv(side, h1, h2)
        return idx, u, v

    def neuron_directions(self, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Nöronların bakış yönleri; kolonu bulunamayanlar düşürülür.

        Döndürür: (idx, taraf, φ, θ); φ 0° yan, +90° ön; θ + sırt (derece).
        """
        idx, side, h1, h2 = self.neuron_columns(idx)
        phi, theta = self.view(h1, h2)
        return idx, side, phi, theta

    def neuron_columns(self, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Nöronların kolonları (hex1, hex2); koordinatı olmayanlar partner oylamasıyla bulunur.

        Döndürür: (idx, taraf, hex1, hex2); kolonu bulunamayanlar düşürülür.
        """
        nn = self.conn.neurons
        idx = np.asarray(idx)
        h1 = nn.hex1.to_numpy()[idx].astype(float)
        h2 = nn.hex2.to_numpy()[idx].astype(float)
        missing = idx[np.isnan(h1)]
        todo = [n for n in missing if n not in self._inferred]
        if todo:
            inf = infer_columns(self.conn, np.array(todo))
            self._inferred.update({int(r.idx): (r.hex1, r.hex2) for r in inf.itertuples()})
            # İkinci tur: kolonu yeni çıkarılan partnerler de oy verir (ör. R7 ← R8).
            still = [n for n in todo if n not in self._inferred]
            if still:
                self._prime_partners(np.array(still))
                inf = infer_columns(self.conn, np.array(still), known=self._inferred)
                self._inferred.update({int(r.idx): (r.hex1, r.hex2) for r in inf.itertuples()})
        for k, n in enumerate(idx):
            if np.isnan(h1[k]) and int(n) in self._inferred:
                h1[k], h2[k] = self._inferred[int(n)]
        ok = ~np.isnan(h1)
        return idx[ok], nn.side.to_numpy()[idx][ok], h1[ok], h2[ok]

    def _prime_partners(self, idx: np.ndarray) -> None:
        """Verilen nöronların koordinatsız partnerlerinin kolonlarını önceden çıkarır."""
        nn = self.conn.neurons
        hexed = nn.hex1.notna().to_numpy()
        W = abs(self.conn.W)
        Wr = W.tocsr()
        partners = set()
        for n in idx:
            partners.update(W.indices[W.indptr[n]:W.indptr[n + 1]])
            partners.update(Wr.indices[Wr.indptr[n]:Wr.indptr[n + 1]])
        todo = [p for p in partners if not hexed[p] and p not in self._inferred]
        if todo:
            inf = infer_columns(self.conn, np.array(todo))
            self._inferred.update({int(r.idx): (r.hex1, r.hex2) for r in inf.itertuples()})
