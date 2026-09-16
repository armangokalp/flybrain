"""Adlandırılmış nöron havuzları: sineğin duyuları ve davranışları.

Tüm eşlemelerin tek kaynağı bu dosyadır. Her havuz, `Connectome.select`
fonksiyonuna verilen bir kriter sözlüğüdür. Gerekçeler docs/02-mimari.md ve
docs/05-veri-kesfi.md belgelerinde.

Kullanım (havuzları doğrular ve boyutlarını yazdırır):
    python -m flybrain.anatomy
"""

import re

import numpy as np

from flybrain.connectome.connectome import Connectome, load_connectome

SENSORY = {
    # Görme: histaminerjik fotoreseptörler; kolonlar Faz 3'te bağlantıdan çıkarılacak.
    "R1_R6": {"type": "R1-R6"},
    "R7": {"type": ["R7p", "R7y", "R7d", "R7_unclear"]},
    "R8": {"type": ["R8p", "R8y", "R8d", "R8_unclear"]},
    # Koku: 53 glomerül tipi (ORN_DA1, ORN_VA2, ...).
    "ORN": {"class": "olfactory", "type": re.compile(r"^ORN_")},
    # Tat: Gr64f+ şeker nöronları LB3b/LB3c, acı nöronları LB1a-d.
    "seker": {"type": ["LB3b", "LB3c"]},
    "aci": {"type": ["LB1a", "LB1b", "LB1c", "LB1d"]},
    # Pekiştirme: PAM ödül, PPL1 ceza.
    "PAM": {"class": "DAN", "type": re.compile(r"^PAM")},
    "PPL1": {"class": "DAN", "type": re.compile(r"^PPL1")},
}

MOTOR = {
    "ileri_yuru": {"type": ["DNp09", "DNg97"]},  # DNg97 = oDN1 (Sapkal 2024)
    "geri_yuru": {"type": "MDN"},  # moonwalker, DNp50
    "hortum": {"type": "MN9"},
    "yutma": {"type": ["MN11D", "MN11V", "MN12D"]},  # yutma pompası (Manzo ve ark. 2012)
    "sarki": {"type": ["pIP10", "vPR6"]},
    "kur": {"type": re.compile(r"^pC1_"), "fruDsx": "coexpress_high"},  # P1 soyu (pMP4)
    "kacis": {"type": "DNp01"},  # Giant Fiber
    "don_sol": {"type": "DNa02", "side": "L"},
    "don_sag": {"type": "DNa02", "side": "R"},
    "timar": {"type": ["DNg62", "DNge078"]},  # aDN1, aDN2 (Hampel 2015)
}


def pools(conn: Connectome, table: dict) -> dict[str, np.ndarray]:
    return {name: conn.select(**criteria) for name, criteria in table.items()}


def main() -> None:
    conn = load_connectome()
    empty = []
    for title, table in (("Duyu", SENSORY), ("Motor", MOTOR)):
        print(f"\n{title} havuzları")
        for name, idx in pools(conn, table).items():
            sub = conn.neurons.iloc[idx]
            nts = sub.nt.value_counts().to_dict()
            print(f"  {name:<12} {len(idx):>5} nöron  tipler={sub.type.nunique():<3} verici={nts}")
            if len(idx) == 0:
                empty.append(name)
    if empty:
        raise SystemExit(f"Boş havuzlar: {empty}")


if __name__ == "__main__":
    main()
