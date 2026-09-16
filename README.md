# flybrain

Bu deneysel projede bir meyve sineğinin (*Drosophila melanogaster*) tam sinir sistemi haritasından simüle edilen bir beyin, bir Instagram hesabını tamamen kendi başına kullanıyor.

- Sinek feed'i **görür**: post görselleri sineğin bileşik gözündeki fotoreseptörlere işlenir.
- Caption'ları **koklar**: her kelime, koku alıcı nöronlara eşlenen bir "koku molekülü" gibi davranır.
- **Davranışıyla** karar verir: ileri yürürse feed'i kaydırır, hortumunu uzatırsa beğenir, kur şarkısı söylerse yorum yapar, kaçarsa takipten çıkar.
- Kendi postlarını ve caption'larını da kendi nöral aktivitesiyle üretir.

Kararları insan, dil modeli ya da eğitilmiş bir yorumlayıcı ağ vermez. Sinirsel aktivite ile Instagram arasındaki bütün eşlemeler sabittir, anatomiye dayanır ve belgelenmiştir. Ayrıntılar için [vizyon ve ilkeler](docs/01-vizyon-ve-ilkeler.md) belgesine bakın.

## Durum

**Faz 0: araştırma ve mimari.** İlerleme için [yol haritası](docs/04-yol-haritasi.md), günlük kayıtlar için [docs/gunluk](docs/gunluk/) klasörüne bakın.

## Belgeler

| Belge | İçerik |
|---|---|
| [01 — Vizyon ve ilkeler](docs/01-vizyon-ve-ilkeler.md) | "Sinek karar verir" ne demek, insan nerede devrede |
| [02 — Mimari](docs/02-mimari.md) | Sistem bileşenleri, duyu ve motor eşlemeleri |
| [03 — Zorluklar](docs/03-zorluklar.md) | Karşılaşılan/beklenen sorunlar ve çözüm yolları |
| [04 — Yol haritası](docs/04-yol-haritasi.md) | Fazlar ve her fazın bitiş kriterleri |
| [Kararlar](docs/kararlar.md) | Alınan tasarım kararlarının kaydı |
| [Kaynaklar](docs/kaynaklar.md) | Veri setleri, makaleler, referans kodlar |
| [Günlük](docs/gunluk/) | Oturum oturum süreç kaydı |

## Veri

Projede Janelia FlyEM ve Google'ın 2026'da yayınladığı **Male CNS v1.0** konnektomu kullanılır (166.000'den fazla nöron; beyin, optik loblar ve ventral sinir kordonu). Veri [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) lisanslıdır; kaynak bilgisi için [kaynaklar](docs/kaynaklar.md) belgesine bakın.

## Lisans

Kod MIT lisanslıdır ([LICENSE](LICENSE)). Konnektom verisinin lisansı CC-BY 4.0'dır.
