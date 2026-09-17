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

- Nöron boyutları: MaleCNS neuPrint girdi tablosu `v1.0/database/neuprint-inputs/Neuprint_Neurons.feather` (yalnızca `bodyId` ve `size` sütunları, ilk 6 parça; `flybrain/connectome/sizes.py`)

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
- Pugliese ve ark. 2025, bioRxiv — [sinir kordonu konnektomu simülasyonlarıyla yürüme ritim devresi](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/) (DNg100, E1/E2/I1 çekirdeği). Kod (MIT): <https://github.com/smpuglie/Pugliese_cpg_2025>. Simülasyon verisi: [Zenodo 22260924](https://zenodo.org/records/22260924). Hız modelimizin kaynağı (K-025); ön bacak MaleCNS tablosu (`wTable_20260210_vncRoisOnly.csv`) doğrulama için indirildi
- McKellar ve ark. 2020, *eLife* 9:e54978 — [hortumun tüm kaslarının motor nöronları](https://elifesciences.org/articles/54978): MN9 rostrum ileri + haustellum açma, MN4 haustellum açma, MN1/MN2 geri çekme, MN3 haustellum bükme
- Zumstein ve ark. 2004, *J Exp Biol* 207:3515 — [sıçramada kuvvet üretimi](https://journals.biologists.com/jeb/article/207/20/3515/14914/Distance-and-force-production-during-jumping-in): TTM, orta bacak ucunda 101 µN, tepeye 8,2 ms
- Tanouye ve Wyman 1980, *J Neurophysiol*; Allen ve ark. 2006, *Curr Opin Neurobiol* — dev lif sistemi, dev lif → TTMn ve PSI elektriksel sinapsları (K-023)
- O'Sullivan ve ark. 2018, *Curr Biol* — [kanat kaslarının şarkı ve uçuştaki çok işlevli kontrolü](https://www.cell.com/current-biology/fulltext/S0960-9822(18)30829-7)
- Azevedo ve ark. 2024, *Nature* 631:360 — [dişi sinir kordonu konnektomu ve motor nöron–kas atlası](https://www.nature.com/articles/s41586-024-07389-x)
- Cheong ve ark. 2024, *eLife* — [MANC'ta inen girdiden motor çıktıya devreler](https://elifesciences.org/articles/96084)
- Lee ve ark. 2025, *Nature Communications* — [bacak propriyosepsiyonu ve dış algı için ayrışan devreler](https://www.nature.com/articles/s41467-025-59302-3) ([açık erişim](https://pmc.ncbi.nlm.nih.gov/articles/PMC12048489/)): FeCO bükülme/açılma algılayıcılarının motor nöronlara bağlantı imzası (K-024)
- Pratt ve ark. 2026, *Nature Communications* — [propriyoseptif sınır dedektörleri](https://www.nature.com/articles/s41467-026-69333-z) ([açık erişim](https://pmc.ncbi.nlm.nih.gov/articles/PMC13009157/)): kıl plakaları, CxHP8
- Mamiya, Gurung ve Tuthill 2018, *Neuron* 100:636 — [bacak propriyosepsiyonunun nöral kodlaması](https://www.cell.com/neuron/fulltext/S0896-6273(18)30782-7): pençe (pozisyon), kanca (yönlü hareket), topuz (titreşim)
- Mamiya ve ark. 2023, *Neuron* — [propriyoseptör seçiciliğinin biyomekanik kökenleri](https://www.cell.com/neuron/fulltext/S0896-6273(23)00542-1)
- Agrawal ve ark. 2020, *eLife* — [bacak propriyosepsiyonunun merkezi işlenmesi](https://elifesciences.org/articles/60299): bükülmüş (0–90°) ve açılmış (90–180°) açıları kodlayan pençe alt tipleri
- Warren ve Göpfert 2024, *J Exp Biol* — [larva kordotonal organının (lch5) mekanik uyarıya spike yanıtları](https://pmc.ncbi.nlm.nih.gov/articles/PMC11418168/): tek nöron hızları 1,5–78 Hz
- Marin ve ark. 2024, *eLife* — [MANC'ın sistematik adlandırması](https://elifesciences.org/reviewed-preprints/97766v1) (SNpp duyu nöronu tipleri)
- Yang ve Clandinin 2018, *Annual Review of Vision Science* — [Drosophila'da temel hareket algılama](https://pmc.ncbi.nlm.nih.gov/articles/PMC8097889/): L1/L2 geçici, L3 kalıcı; Mi1/Tm3 çift fazlı (K-027)
- Arenz ve ark. 2017, *Current Biology* 27:929–944 — [hareket algılayıcılarının zamansal ayarı girdi hücrelerinin dinamiğinden gelir](https://www.sciencedirect.com/science/article/pii/S0960982217300866): T5'e giden Tm9 alçak geçiren, Tm1/Tm2/Tm4 bant geçiren (Z-25)
- Nikolaev ve ark. 2009, *PLoS One* — [ağ adaptasyonu, sinek gözünde doğal uyaranların zamansal temsilini iyileştirir](https://pmc.ncbi.nlm.nih.gov/articles/PMC2628722/): fotoreseptör ve lamina adaptasyonu saniyeler içinde
- Stowers ve ark. 2017, *Nature Methods* — [serbest hareket eden hayvanlar için sanal gerçeklik (FreemoVR)](https://www.nature.com/articles/nmeth.4399)
- von Reyn ve ark. 2014, *Nature Neuroscience* 17:962–970 — [eylem seçimi için spike zamanlaması mekanizması](https://www.nature.com/articles/nn.3741): yaklaşan uyarana kaçışta dev lifin kısa kalkışı zorlaması; yaklaşan disk uyaranımızın türü (Z-25)
- Klapoetke ve ark. 2017, *Nature* 551:237–241 — [radyal hareket karşıtlığıyla çok seçici yaklaşma algılama](https://www.nature.com/articles/nature24626) ([açık erişim](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7457385/)): LPLC2 dışa yayılan harekete seçici; kararma, daralma ve geniş alan kaymasına yanıt yok (Z-25, K-030)
- Lebestky ve ark. 2009, *Neuron* — [iki uyarılmışlık biçimi, dopamin reseptörü DopR tarafından ayrı devreler üzerinden zıt yönde düzenlenir](https://pubmed.ncbi.nlm.nih.gov/19945394/) ([açık erişim](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2908595/)): DopR kaybı tekrarlanan irkilmeden sonraki uyarılmışlığı artırıyor; bu etki elipsoid gövdede (Z-35)

## Gövde modelleri

- Wang-Chen ve ark. 2024, *Nature Methods* — [NeuroMechFly v2](https://www.nature.com/articles/s41592-024-02497-y). Kütüphane: [FlyGym](https://github.com/NeLy-EPFL/flygym) (Apache-2.0), belgeler: <https://neuromechfly.org/>
- FlyMimic kas-iskelet modeli: [Drosophila bacak hareketinin kas-iskelet simülasyonu](https://arxiv.org/html/2509.06426) (arXiv 2509.06426). FlyGym 2.1 içinde `assets/model/musculoskeletal`; bacak kas geometrimizin kaynağı (K-019 eki)
- Vaxenburg ve ark. 2025, *Nature* — [flybody: tüm gövde fizik simülasyonu](https://www.nature.com/articles/s41586-025-09029-4). Kod: <https://github.com/TuragaLab/flybody>. Uçuş kontrolcüsü eğitilmiş olduğu için kullanılmıyor (Z-26).

## Referans uygulamalar

- [vshapenko/flypoke](https://github.com/vshapenko/flypoke): NumPy tabanlı, bağımlılığı az FlyWire LIF simülasyonu (MIT)
- [snedea/flybrain](https://github.com/snedea/flybrain): tarayıcıda çalışan etkileşimli LIF simülasyonu
- [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain): Brian2, PyTorch, NEST GPU karşılaştırmaları

## Bağlam

- [Eon Systems: sanal gövdeli beyin emülasyonu](https://eon.systems/updates/embodied-brain-emulation) (Mart 2026): gövde hareketlerinin taklit öğrenmesiyle eğitilmiş kontrolcülerden geldiğini ekip kendisi belirtiyor. [K-019](kararlar.md#k-019--3d-gövde-neuromechfly-doğrudan-motor-nöron--kas--eklem) kararının arka planı.
- [Konnektom sonrası viral demoların analizi](https://www.stork.ai/blog/google-unleashed-a-fly-brain-chaos-ensued): bu demoların çoğunun çıktıyı eğitilmiş bir yapay zekâyla yorumladığına dair eleştiri. [K-003](kararlar.md#k-003--eğitilmiş-yorumlayıcı-ve-dil-modeli-yok) kararının arka planı.
