# Kaynaklar

## Veri setleri

### Male CNS v1.0 (birincil)

- Janelia FlyEM & Google Research, 2026. *Cell*. DOI: [10.1016/j.cell.2026.08.015](https://doi.org/10.1016/j.cell.2026.08.015)
- Lisans: CC-BY 4.0
- Portal: <https://male-cns.janelia.org/>
- İndirmeler: <https://male-cns.janelia.org/download/>
- Proje sayfası: <https://www.janelia.org/project-team/flyem/male-cns-connectome>
- Duyuru: [Google Research blog, 3 Eylül 2026](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/)
- neuPrint veri seti adı: `male-cns:v1.0` (etkileşimli erişim için ücretsiz hesap + token gerekiyor; toplu indirme için gerekmiyor)

Kullanılacak dosyalar (token gerektirmez):

| Dosya | Boyut |
|---|---|
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 13 MB |
| `body-neurotransmitters-male-cns-v1.0.feather` | 42 MB |
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1,1 GB |

Taban adres: `https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/`

### FlyWire FAFB v783 (yedek / doğrulama)

- Dorkenwald ve ark. 2024, *Nature* 634:124–138
- Schlegel ve ark. 2024, *Nature* 634:139–152 (anotasyonlar): <https://github.com/flyconnectome/flywire_annotations>
- Bağlantı tablosu: [Zenodo 10676866](https://doi.org/10.5281/zenodo.10676866)

## Modeller ve makaleler

- Shiu ve ark. 2024, *Nature* 634:210–219 — tüm beyin LIF modeli. Kod: <https://github.com/philshiu/Drosophila_brain_model>
- Eckstein ve ark. 2024, *Cell* 187:2574–2594 — EM görüntülerinden nörotransmitter tahmini
- Bidaye ve ark. 2014, *Science* — geri yürüme (MDN)
- Bidaye ve ark. 2020, *Neuron* — ileri yürüme ve dönme için inen nöronlar
- Rayshubskiy ve ark. 2020 — DNa02 ve dönme
- Hampel ve ark. 2015, *eLife* — anten temizleme devresi

## Referans uygulamalar

- [vshapenko/flypoke](https://github.com/vshapenko/flypoke): NumPy tabanlı, bağımlılığı az FlyWire LIF simülasyonu (MIT)
- [snedea/flybrain](https://github.com/snedea/flybrain): tarayıcıda çalışan etkileşimli LIF simülasyonu
- [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain): Brian2, PyTorch, NEST GPU karşılaştırmaları

## Bağlam

- [Konnektom sonrası viral demoların analizi](https://www.stork.ai/blog/google-unleashed-a-fly-brain-chaos-ensued): bu demoların çoğunun çıktıyı eğitilmiş bir yapay zekâyla yorumladığına dair eleştiri. [K-003](kararlar.md#k-003--eğitilmiş-yorumlayıcı-ve-dil-modeli-yok) kararının arka planı.
