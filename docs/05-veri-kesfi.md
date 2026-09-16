# 05 — Veri Keşfi (MaleCNS v1.0)

> Faz 1 çıktısı, 2026-09-16. Yeniden üretmek için:
> `python -m flybrain.connectome.download && python -m flybrain.connectome.build && python -m flybrain.anatomy`

## Ham dosyalar

| Dosya | Satır | Not |
|---|---|---|
| body-annotations | 211.577 gövde, 36 sütun | Yalnızca `status == "Traced"` olan **165.122** nöron kullanıldı. Kalanlar yetim parçalar, glia vb. |
| body-neurotransmitters | 1.835.518 | 164.620 izlenmiş nöron kapsanıyor; kalan 502 nöron varsayılan işareti alıyor |
| connectome-weights | 151.856.684 segment çifti | İzlenmiş nöronlar arasında **25,6 milyon bağlantı, 124 milyon sinaps** (yayınlanan 125 milyonla uyumlu) |

## Bağlantı eşiği

| En az sinaps | Bağlantı | Sinaps |
|---|---|---|
| 1 | 25.563.197 | 124.025.046 |
| 3 | 10.511.038 | 104.213.652 |
| **5** | **6.235.682** | **89.731.551** |
| 10 | 2.749.407 | 67.173.142 |

5 sinaps eşiği (Shiu ve ark. yaklaşımı) sinapsların %72'sini koruyor, bağlantı sayısını ise 4'te 1'e indiriyor. 5 veya daha fazla sinapslı 33 otapsın (nöronun kendine bağlantısı) çıkarılmasıyla önbellekte **6.235.649** bağlantı kaldı.

Önbellek üretimi 3 saniye sürüyor ve bellek kullanımı en fazla 4,4 GB'a çıkıyor. Diskteki önbellek boyutu 54 MB.

## Nörotransmitterler (izlenmiş nöronlar, konsensüs tahmini)

| Verici | Nöron | Modeldeki işaret |
|---|---|---|
| asetilkolin | 103.718 | + |
| glutamat | 29.296 | − |
| GABA | 22.055 | − |
| histamin | 5.910 | − |
| belirsiz | 3.100 | Tekil tahmine düşülür; o da belirsizse + |
| dopamin | 392 | + (varsayım, K-008) |
| oktopamin | 101 | + (varsayım, K-008) |
| serotonin | 48 | + (varsayım, K-008) |

## Anotasyonlardan gelen yararlı sütunlar

- `assignedOlHex1/2`: optik lob kolon koordinatları (1–36 × 1–39). **15 kolon tipinde** mevcut (L1, L2, L5, Mi1, Mi4, Mi9, Tm1, Tm2, Tm9, Tm20, T1, C3; yalnızca sağda L3, C2, Tm4). Göz başına yaklaşık **890 kolon** var.
- `fruDsx`: kur yapma genlerinin ifadesi, P1 nöronlarını ayırt etmek için kullanılıyor.
- `somaLocation`: nöral portre görseli için 3B soma konumları (8 nm voksel).
- `synonyms`: literatürdeki eski adlar. Aday nöronların eşleştirilmesinde kilit rol oynadı.
- `receptorType`: koku nöronlarında boş, yalnızca bacak ve kanat tat kıllarında dolu.

## Doğrulanan nöron havuzları

Kaynak: [`flybrain/anatomy.py`](../flybrain/anatomy.py)

### Motor

| Havuz | Tipler | Nöron | Bulunuş şekli |
|---|---|---|---|
| ileri_yuru | DNp09, **DNg97** | 4 | oDN1 bu veri setinde `DNg97` adında (eşanlam: "Sapkal 2024: oDN1") |
| geri_yuru | MDN | 4 | eşanlam: DNp50 |
| hortum | MN9 | 2 | doğrudan |
| sarki | pIP10, vPR6 | 10 | pIP10 inen nöron, vPR6 ventral sinir kordonu ara nöronu |
| kur (P1) | pC1_* (fru+dsx yüksek) | 49 | Erkekte P1 soyu `pC1_*` tipleri altında (Yu 2010: pMP4 / Cachero 2010: pMP-e) |
| kacis | DNp01 | 2 | "Giant Fiber" |
| don_sol / don_sag | DNa02 | 1 + 1 | Soma tarafına göre ayrıldı |
| timar | **DNg62**, **DNge078** | 4 | aDN1 ve aDN2 bu adlarla (eşanlam: Hampel 2015) |

### Duyu

| Havuz | Tipler | Nöron | Not |
|---|---|---|---|
| R1_R6 | R1-R6 | 1.394 | Sağ 893, sol 501: sol göz eksik |
| R7 / R8 | p/y/d/belirsiz alt tipleri | 1.299 / 1.329 | Renk alt tipleri (soluk/sarı/dorsal) mevcut |
| ORN | 53 glomerül tipi | 2.635 | Kelime→koku alfabesi |
| seker | LB3b, LB3c | 34 | Gr64f+ dudak tat nöronları (2026 tat konnektomu çalışması) |
| aci | LB1a–d | 38 | 2 nöronun tahmini vericisi serotonin çıktı; tuhaf ama önemsiz |
| PAM / PPL1 | PAM* / PPL1* | 316 / 16 | Ödül / ceza dopamin nöronları |

## Duyudan motora sinaptik mesafe

Her hücre "en kısa yol / yalnızca uyarıcı bağlantılarla en kısa yol" biçiminde, adım sayısı olarak verilmiştir.

| Duyu | ileri | geri | hortum | şarkı | kur | kaçış | dön-sol | dön-sağ | tımar |
|---|---|---|---|---|---|---|---|---|---|
| seker | 2/3 | 3/3 | **2/2** | 3/3 | 2/3 | 3/3 | 2/2 | 3/3 | 2/3 |
| aci | 3/3 | 3/3 | 2/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 2/3 |
| ORN | 3/3 | 3/3 | 3/3 | 3/3 | 2/2 | 3/3 | 3/3 | 3/3 | 2/3 |
| R1_R6 | 4/– | 4/– | 5/– | 4/– | 4/– | 4/– | 4/– | 4/– | 5/– |
| R7 | 3/– | 3/– | 4/– | 3/– | 3/– | 3/– | 3/– | 3/– | 4/– |
| R8 | 3/– | 3/– | 4/– | 3/– | 3/– | 3/– | 3/– | 3/– | 3/– |
| PAM | 3/3 | 2/2 | 3/3 | 2/2 | 2/2 | 3/3 | 2/2 | 2/3 | 3/3 |

### Sonuçlar

1. **Şeker → MN9 arasında 2 adımlık, tamamen uyarıcı bir yol var.** Faz 2'deki doğrulama deneyinin (şeker uyarımı hortum motor nöronunu ateşletmeli) topolojik ön koşulu sağlanıyor.
2. **Fotoreseptörlerden hiçbir yere uyarıcı yol yok.** Fotoreseptörlerin ilk sinapsı ketleyici (histamin). Sessiz bir modelde bu, görme sinyalinin ilk sinapsta kaybolması demek. Ayrıntı ve çözüm seçenekleri için [Z-02](03-zorluklar.md#z-02--görme-sinyali-merkezi-beyne-ulaşabilecek-mi-) maddesine bakın.
3. **Ağ çok sıkı bağlı.** Her duyu, beynin yaklaşık %98'ine en fazla birkaç adımda ulaşıyor. Hangi davranışın ortaya çıkacağını topoloji değil, **ağırlıklar ve işaretler** belirleyecek.
