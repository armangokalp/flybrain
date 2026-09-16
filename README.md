# flybrain

Bu deneysel projede bir meyve sineğinin (*Drosophila melanogaster*) tam sinir sistemi haritasından simüle edilen bir beyin, bir Instagram hesabını tamamen kendi başına kullanıyor.

- Sinek feed'i **görür**: post görselleri sineğin bileşik gözündeki fotoreseptörlere işlenir.
- Caption'ları **koklar**: her kelime, koku alıcı nöronlara eşlenen bir "koku molekülü" gibi davranır.
- **Davranışıyla** karar verir: ileri yürürse feed'i kaydırır, hortumunu uzatırsa beğenir, kur şarkısı söylerse yorum yapar, kaçarsa takipten çıkar.
- Kendi postlarını ve caption'larını da kendi nöral aktivitesiyle üretir.
- Bütün bunları **3D bir gövdede** görebilirsiniz. Gövdeyi yalnızca simüle edilen motor nöronlar hareket ettirir; animasyon ya da eğitilmiş hareket programı yoktur. Beyin aktivitesi de her nöronun gerçek konumunda izlenebilir.

Kararları insan, dil modeli ya da eğitilmiş bir yorumlayıcı ağ vermez. Sinirsel aktivite ile Instagram arasındaki bütün eşlemeler sabittir, anatomiye dayanır ve belgelenmiştir. Ayrıntılar için [vizyon ve ilkeler](docs/01-vizyon-ve-ilkeler.md) belgesine bakın.

## Durum

- ✅ **Faz 0:** araştırma ve mimari
- ✅ **Faz 1:** konnektom veri hattı (165.122 nöron, 6,2 milyon bağlantı)
- ✅ **Faz 2:** simülasyon çekirdeği (neredeyse gerçek zamanlı, kararlı beyin ayarı)
- ✅ **Faz 3:** duyu kodlayıcıları (görsel → göz, caption → koku, bildirim → dopamin)
- ✅ **Faz 4:** motor kod çözücü (kas grupları → Instagram eylemleri, eylem bütçesi, eşik homeostazı)
- ⏭️ **Faz 5:** 3D gövde (motor nöron → kas → eklem, NeuroMechFly) — sürüyor
- **Faz 6:** görselleştirme ve kayıt (3D sinek, 3D beyin, sineğin gördüğü)
- **Faz 7:** yerel kum havuzu ve korku tepkisi
- **Faz 8–10:** Instagram bağlantısı, içerik üretimi, öğrenme

İlerleme için [yol haritası](docs/04-yol-haritasi.md), günlük kayıtlar için [docs/gunluk](docs/gunluk/) klasörüne bakın.

## Kurulum

Python 3.12 veya 3.13 gerekir.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m flybrain.connectome.download   # yaklaşık 1,1 GB, data/raw/
.venv/bin/python -m flybrain.connectome.build      # önbellek, data/cache/
.venv/bin/python -m flybrain.anatomy               # nöron havuzlarını doğrular
.venv/bin/python -m pytest
```

## Belgeler

| Belge | İçerik |
|---|---|
| [01 — Vizyon ve ilkeler](docs/01-vizyon-ve-ilkeler.md) | "Sinek karar verir" ne demek, insan nerede devrede |
| [02 — Mimari](docs/02-mimari.md) | Sistem bileşenleri, duyu ve motor eşlemeleri |
| [03 — Zorluklar](docs/03-zorluklar.md) | Karşılaşılan/beklenen sorunlar ve çözüm yolları |
| [04 — Yol haritası](docs/04-yol-haritasi.md) | Fazlar ve her fazın bitiş kriterleri |
| [05 — Veri keşfi](docs/05-veri-kesfi.md) | MaleCNS verisinin analizi, doğrulanan nöron havuzları |
| [06 — Simülasyon](docs/06-simulasyon.md) | LIF motoru, kalıcı çekici bulgusu, ayar taramaları |
| [07 — Duyular](docs/07-duyular.md) | Göz geometrisi, görme/koku/ödül kodlayıcıları ve deneyleri |
| [08 — Motor](docs/08-motor.md) | Kas grubu okuması, eylem bütçesi, kalibrasyon ve homeostaz |
| [09 — Gövde](docs/09-govde.md) | 3D gövde, motor nöron → kas → eklem, yürüme ritmi deneyleri |
| [Kararlar](docs/kararlar.md) | Alınan tasarım kararlarının kaydı |
| [Kaynaklar](docs/kaynaklar.md) | Veri setleri, makaleler, referans kodlar |
| [Günlük](docs/gunluk/) | Oturum oturum süreç kaydı |

## Veri

Projede Janelia FlyEM ve Google'ın 2026'da yayınladığı **Male CNS v1.0** konnektomu kullanılır (166.000'den fazla nöron; beyin, optik loblar ve ventral sinir kordonu). Veri [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) lisanslıdır; kaynak bilgisi için [kaynaklar](docs/kaynaklar.md) belgesine bakın.

## Lisans

Kod MIT lisanslıdır ([LICENSE](LICENSE)). Konnektom verisinin lisansı CC-BY 4.0'dır. 3D gövde [FlyGym / NeuroMechFly](https://github.com/NeLy-EPFL/flygym) (Apache-2.0) ile simüle edilir.
