"""K-036'nın ön koşulu: aynı kelime farklı beyin durumlarında farklı yanıt alıyor mu?

Yorumun kelimeleri koklanarak seçiliyor ve koklama sineğin o anki durumunda yapılıyor. Duygunun
kelime seçimini gerçekten değiştirdiğini göstermek için aynı kelime listesi iki durumda
koklanıyor:

  - **nötr:** sinek posta bakıyor, olağan durum.
  - **korku:** koklamadan hemen önce ekranda yaklaşan bir disk (escape.py'deki uyaran).

Her durum iki kez ölçülüyor. Aynı durumun iki ölçümü arasındaki sıralama benzerliği "gürültü
tabanı"; durumlar arasındaki benzerlik bundan belirgin biçimde düşükse durum kelime seçimini
değiştiriyor demektir.

Kullanım:
    python -m flybrain.experiments.comment [--kelime 10] [--seed 8003] [--tekrar 2]
"""

import argparse
import itertools

import numpy as np

SETTLE_MS = 2000.0   # yerleştirmeden sonra bekleme (insta/session.py ile aynı)
AFTER_LOOM_MS = 200.0


def _rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman sıra bağıntısı (scipy'siz)."""
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    ra, rb = ra - ra.mean(), rb - rb.mean()
    denom = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / denom) if denom else float("nan")


def run(n_words: int, seed: int, repeats: int, sniff_ms: float | None = None) -> dict:
    from flybrain.body.phone import FeedPost, fit, post_box
    from flybrain.body.scene import SceneConfig, pixel_directions
    from flybrain.experiments.calibrate import CAL_SEED, make_post
    from flybrain.experiments.embodied_calibrate import _viewer
    from flybrain.experiments.escape import looming_video
    from flybrain.motor.comment import CommentWriter
    from flybrain.motor.mood import MOODS, MoodCalibration, MoodReadout
    from flybrain.motor.selector import WINDOW_MS
    from flybrain.senses.olfaction import tokenize

    viewer = _viewer(seed)
    fly = viewer.fly
    cfg = SceneConfig()
    mood = MoodReadout(fly.conn, MoodCalibration.load())
    writer = CommentWriter(fly, viewer.readout, mood)
    if sniff_ms:  # 300 ms'de kelimelerin çoğu 0,000 Hz veriyor: ölçümün çözünürlüğü yok
        writer.sniff_ms = sniff_ms

    post = make_post(0, CAL_SEED)
    # Ekran akışı FeedPost bekliyor; make_post kalibrasyonun Post'unu döndürüyor.
    ekran_postu = FeedPost(post.image, caption=post.caption)
    words = [w for w in dict.fromkeys(tokenize(post.caption)) if len(w) >= 2][:n_words]
    if len(words) < n_words:  # caption kısaysa başka postlardan tamamla
        for k in range(1, 20):
            for w in tokenize(make_post(k, CAL_SEED).caption):
                if len(w) >= 2 and w not in words:
                    words.append(w)
            if len(words) >= n_words:
                break
    words = words[:n_words]

    top, bottom, left, right = post_box(cfg.texture_shape)
    rows, cols = np.mgrid[top:bottom, left:right]
    dirs = pixel_directions(cfg, rows, cols)
    background = fit(post.image, right - left, bottom - top)

    scores: dict[tuple[str, int], np.ndarray] = {}
    moods: dict[tuple[str, int], str] = {}
    for state, rep in itertools.product(("notr", "korku"), range(repeats)):
        fly.show_post(ekran_postu)
        fly.reset()
        fly.run(SETTLE_MS)
        if state == "korku":
            video, t_coll = looming_video(background, dirs)
            fly.play_video(video)
            fly.run(t_coll + AFTER_LOOM_MS)
        counts = np.zeros(fly.conn.n, dtype=np.int64)
        fly.spike_counter = counts
        fly.run(WINDOW_MS)
        fly.spike_counter = None
        moods[(state, rep)] = mood.dominant(counts, WINDOW_MS)[0]
        scores[(state, rep)] = np.array([writer.sniff(w) for w in words])
        print(f"  {state} tekrar {rep}: baskın duygu {moods[(state, rep)]}, "
              f"yaklaşma ort. {scores[(state, rep)].mean():+.3f}", flush=True)

    fly.eyes.close()
    fly.body.close()
    out = {"kelimeler": words, "skorlar": {f"{s}-{r}": v.tolist() for (s, r), v in scores.items()},
           "duygular": {f"{s}-{r}": m for (s, r), m in moods.items()}, "moods": list(MOODS)}
    if repeats >= 2:
        out["ayni_durum"] = [_rank_corr(scores[("notr", 0)], scores[("notr", 1)]),
                             _rank_corr(scores[("korku", 0)], scores[("korku", 1)])]
    out["durumlar_arasi"] = [_rank_corr(scores[("notr", i)], scores[("korku", j)])
                             for i in range(repeats) for j in range(repeats)]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kelime", type=int, default=10)
    ap.add_argument("--seed", type=int, default=8003)
    ap.add_argument("--tekrar", type=int, default=2)
    ap.add_argument("--koklama", type=float, default=None,
                    help="koklama penceresi (ms; varsayılan CommentWriter.sniff_ms)")
    args = ap.parse_args()
    r = run(args.kelime, args.seed, args.tekrar, args.koklama)

    print("\nkelime başına yaklaşma skoru (ileri − geri − çıkış, Hz)")
    keys = sorted(r["skorlar"])
    print(f"{'kelime':16} " + " ".join(f"{k:>10}" for k in keys))
    for i, w in enumerate(r["kelimeler"]):
        print(f"{w:16} " + " ".join(f"{r['skorlar'][k][i]:10.3f}" for k in keys))
    if "ayni_durum" in r:
        print(f"\naynı durumun iki ölçümü (gürültü tabanı): {[round(v, 2) for v in r['ayni_durum']]}")
    print(f"durumlar arası sıralama benzerliği: {[round(v, 2) for v in r['durumlar_arasi']]}")
    print(f"baskın duygular: {r['duygular']}")


if __name__ == "__main__":
    main()
