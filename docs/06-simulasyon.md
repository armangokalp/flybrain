# 06 — Simülasyon Çekirdeği ve Kararlılık (Faz 2)

> 2026-09-16. Kod: [`flybrain/sim/lif.py`](../flybrain/sim/lif.py), deney: [`flybrain/experiments/stability.py`](../flybrain/experiments/stability.py)

## Motor

- Shiu ve ark. LIF modeli; adım içi sıra Brian2 ile aynı (durum güncellemesi → eşik → gecikmeli iletim + Poisson → sıfırlama).
- Doğrusal denklemler için adım başına tam çözüm.
- Olay güdümlü: yalnızca ateşleyen nöronların çıkış sütunları toplanıyor.
- Numba ile derleniyor; beyin durumu `run()` çağrıları arasında korunuyor.
- İki **isteğe bağlı** biyolojik mekanizma eklendi. İkisi de varsayılan olarak kapalı; kapalıyken model Shiu modeliyle birebir aynı:
  - **Kısa süreli sinaptik depresyon (STD):** Hızlı ateşleyen nöronun sinapsları yorulur (`std_u`, `std_tau_ms`).
  - **Ateşleme hızı adaptasyonu (SFA):** Her spike bir potasyum benzeri akımı artırır ve nöron yavaşlar (`adapt_mv`, `adapt_tau_ms`).
- Birim testleri: [`tests/test_lif.py`](../tests/test_lif.py). Sessiz ağ sessiz kalıyor, gecikme tam 18 adım, refrakter sınır doğru, tohum tekrarlanabilir, STD ve SFA beklenen biçimde çalışıyor.

## Performans

Apple Silicon, tek çekirdek: **simülasyonun 1 saniyesi yaklaşık 1,2 saniye sürüyor.** Bu, bir posta 500 ms "bakmanın" yaklaşık 0,6 saniyede hesaplanması demek; gerçek zamana çok yakın. Ağır aktivitede (her saniye 1 milyon spike) bile 1,3 saniyeyi geçmiyor.

**Güncelleme (2026-09-17, Z-21):** Durum güncellemesi artık nöron parçaları üzerinde paralel çalışıyor.
- **Dallanmasız hızlı yol:** Adaptasyon ve tonik akım yoksa (projenin ayarı) güncelleme bu terimleri atlıyor.
- **Sonuç değişmiyor:** Ateşleyen nöronlar parçaların sırasıyla birleştiriliyor. Sonuç, iş parçacığı sayısından bağımsız olarak eski sıralı hesapla bit düzeyinde aynı; spike sayıları, spike zamanları ve bütün durum değişkenleri karşılaştırıldı.
- **Ölçüm** (gövdeli görmenin girdisi: 7.378 görme nöronu, değişken hızlar, 1 sn): eski 2,4 sn, yeni 1,3 sn (4 iş parçacığı). Adaptasyonlu ayarda 1,5 kat.
- **İş parçacığı sayısı:** Ana süreçte 4 (`LIF_THREADS`); bu makinede (4 performans + 6 verimlilik çekirdeği) daha fazlası bellek bant genişliğine takılıyor. Deneylerin süreç havuzlarında 1. `FLYBRAIN_LIF_THREADS` ortam değişkeniyle değiştirilebilir.
- **Denenip bırakılanlar:** Dinlenimdeki nöronları atlamak sonucu değiştirmiyordu ama dallanmalar yüzünden 2 kat yavaşlattı. Poisson çekilişlerini seyreltmek (~0,2 sn/sn kazanç) rastgele sayı akışını değiştireceği için yapılmadı.

## Bulgu 1: Shiu ağırlıklarıyla beyin kalıcı bir çekiciye kilitleniyor

Orijinal parametrelerle (w_syn = 0,275 mV) 34 şeker nöronu uyarıldı:

- MN9 (hortum) sol 166 Hz, sağ 18 Hz ateşledi. Acı uyarımında sol 14 Hz, sağ 0 Hz. **Seçicilik doğru yönde.**
- Ancak beynin yaklaşık **16 bin nöronu** aktif oldu ve uyarım kesildikten sonra **yaklaşık 12 bin nöron aynı hızda ateşlemeye devam etti.**

Uyarım 500. ms'de kesildi; 50 ms'lik pencerelerle ölçüm:

| zaman | aktif nöron | spike | MN9 L/R (Hz) |
|---|---|---|---|
| 0–50 ms | 928 | 1.829 | 120 / 20 |
| 100–150 ms | 11.581 | 37.153 | 180 / 40 |
| 450–500 ms | 12.182 | 50.226 | 160 / 20 |
| **550–600 ms (uyarım yok)** | **12.119** | **49.783** | 0 / 0 |
| **950–1000 ms (uyarım yok)** | **12.378** | **50.949** | 0 / 0 |

### Çekiciyi kimler oluşturuyor?

- Girdiden bağımsız: koku uyarımı ve rastgele 200 nöron uyarımı sonrası kalıcı kümelerin **%97'si ortak**.
- Merkezi **koku lobunda**: asetilkolinerjik yerel ara nöronlar (`lLN1_bc`, 30 nöron, ~400 Hz; vericileri deneysel olarak doğrulanmış), projeksiyon nöronları ve aşağı akışta Kenyon hücreleri.
- Aralarında yüzlerce sinapslı karşılıklı uyarıcı bağlantılar var (ör. `lLN2T_c` ↔ `v2LN30`: 953 / 517 sinaps). Tek bir spike karşı tarafı ateşletmeye yetiyor.
- `lLN1_bc` çıkışını kapatmak çekiciyi yalnızca küçültüyor; sorun dağıtık.
- Vericisi bilinmeyen 2.524 nöronu (çıkış sinapslarının %0,72'si) uyarıcı yerine devre dışı saymak kararlılık sınırını biraz yukarı itiyor ama çözmüyor.

**Olası neden:** Model FlyWire'ın sinaps sayılarına göre ayarlanmıştı. MaleCNS izlenmiş nöronlar arasında 124 milyon sinaps sayıyor ve en az 5 sinapslı bağlantı başına medyan 9 sinaps var. Bir nöron başına ortalama 543 girdi sinapsı düşüyor. Ayrıca doğrusal modelde gerçek sinapslardaki doyum ve yorulma yok.

## Bulgu 2: Global ağırlık ölçeği tek başına dar bir pencere bırakıyor

500 ms uyarım, 300 ms bekleme, sonraki 200 ms'de hâlâ aktif nöron sayısı ("kalıcı"):

| ölçek | MN9 şeker L/R | MN9 acı L/R | kalıcı (şeker) | kalıcı (acı) |
|---|---|---|---|---|
| 1,0 | 172 / 16 | 22 / 0 | 13.097 | 13.492 |
| 0,75 | 132 / 6 | 0 / 0 | 3.024 | 10.355 |
| 0,6 | 64 / 0 | 0 / 0 | 0 | 7.758 |
| 0,5 | 8 / 0 | 0 / 0 | 0 | 0 |
| ≤ 0,4 | 0 / 0 | 0 / 0 | 0 | 0 |

## Bulgu 3: Sinaptik depresyon ve adaptasyon kilitlenmeyi çözüyor ama sinyali de söndürüyor

- **STD** (ölçek 1,0; U = 0,2; τ = 800 ms): 5 farklı uyarımda kalıcılık tamamen kayboldu, fakat şeker→MN9 10 Hz'e, acı→MN9 4 Hz'e indi. Ayırt edilebilirlik zayıf.
- **SFA** (ölçek 0,7; Δa = 4 mV; τ = 400 ms): kalıcılık tamamen kayboldu, fakat şeker→MN9 4 Hz'e indi.

Genel örüntü: kilitlenmeyi söndüren her mekanizma, şeker→MN9 yanıtını da zayıflatıyor. İkisi de aynı güçlü uyarıcı bağlantılardan besleniyor.

## Bulgu 4: Asıl ölçüt olan ayırt edilebilirlik, düşük ölçekte en iyi

Caption tasarımımızın gerektirdiği ölçüt, farklı kelimelerin (kokuların) sinekte farklı tepkiler üretmesi. Bunu ölçmek için her biri 3 rastgele glomerülden oluşan (77–161 ORN) 8 yapay koku kullanıldı. Her ayarda 3'er deneme yapıldı. Okuma, 1.314 inen nöronun 500 ms'lik hız vektörüyle, en yakın merkez sınıflandırmasıyla yapıldı; şans düzeyi %12,5.

| ayar | doğruluk | aktif inen nöron | kalıcı (en çok) |
|---|---|---|---|
| ölçek 0,4 | **%92** | 104 | 3.727 |
| ölçek 0,5 | %67 | 160 | 5.336 |
| ölçek 0,6 | %42 | 242 | 7.658 |
| ölçek 0,7 | %42 | 297 | 9.693 |
| ölçek 1,0 | %46 | 402 | 13.664 |
| 1,0 + STD (0,2 / 800) | %46 | 264 | 181 |
| 0,7 + SFA (2 / 400) | %67 | 295 | 4.964 |
| 0,7 + SFA (4 / 400) | %33 | 235 | 0 |

**Dikkat:** Küçük bir koku (3 glomerül) bile, 0,4 ölçeğinde dahi kalıcı çekiciyi tetikliyor. Koku sistemi bu modelde çok kolay kilitleniyor.

**Rastlantısallık notu:** Kritik sınıra yakın ayarlarda aynı uyarım bir denemede çekiciye düşüp diğerinde düşmeyebiliyor. Bu yüzden sonuçlar birden fazla tohumla ölçülmeli.

## Bulgu 5: Ayrıntılı tarama

Yeniden üretmek için: `python -m flybrain.experiments.stability --grid temel --workers 5` (5 işçiyle yaklaşık 8 dakika).

Protokol:
- Tat: şeker ve acı nöronlarının 3'er denemesi. MN9 değeri, iki MN9 nöronunun ortalamasıdır.
- Koku: 8 koku × 3 deneme.
- Her denemede 500 ms uyarım (ilk 200 ms ayrıca ölçülür), 300 ms bekleme, ardından 200 ms kalıcılık ölçümü.
- "Kalıcı" sütunları, tüm denemeler içindeki en kötü değeri gösterir.

SFA: ateşleme hızı adaptasyonu (Δa mV / τ ms). STD: sinaptik depresyon (U / τ ms).

| ayar (ölçek + mekanizma) | MN9 şeker (Hz) | MN9 acı (Hz) | koku doğruluk 200 / 500 ms | kalıcı nöron (koku) | kalıcı nöron (tat) |
|---|---|---|---|---|---|
| 0,40 | 0 | 0 | %92 / %88 | 3.736 | 0 |
| 0,40 + SFA 1/400 | 0 | 0 | %88 / %92 | 2.044 | 0 |
| **0,40 + SFA 2/400** | 0 | 0 | **%92 / %92** | **0** | **0** |
| **0,40 + STD 0,1/800** | 0 | 0 | %83 / %83 | **0** | **0** |
| 0,45 | 0 | 0 | %67 / %83 | 4.527 | 0 |
| 0,45 + SFA 1/400 | 0 | 0 | %75 / %100 | 2.549 | 0 |
| 0,45 + SFA 2/400 | 0 | 0 | %71 / %88 | 1.400 | 0 |
| **0,45 + STD 0,1/800** | 0 | 0 | **%96 / %96** | **0** | **0** |
| 0,50 | 4,0 | 0 | %62 / %83 | 5.371 | 89 |
| 0,50 + SFA 1/400 | 0 | 0 | %79 / %88 | 3.357 | 0 |
| 0,50 + SFA 2/400 | 0 | 0 | %79 / %88 | 2.006 | 0 |
| 0,50 + STD 0,1/800 | 0 | 0 | %79 / %79 | 84 | 0 |
| 0,55 | 16,3 | 0 | %67 / %88 | 6.741 | 6.170 |
| 0,55 + SFA 1/400 | 0,7 | 0 | %71 / %92 | 3.881 | 0 |
| 0,55 + SFA 2/400 | 0,3 | 0 | %67 / %71 | 2.582 | 0 |
| 0,55 + STD 0,1/800 | 0 | 0 | %88 / %88 | 202 | 0 |
| 0,60 | 31,0 | 0 | %33 / %42 | 7.642 | 7.744 |
| 0,60 + SFA 1/400 | 3,3 | 0 | %29 / %25 | 4.527 | 4.220 |
| 0,60 + SFA 2/400 | 2,0 | 0 | %62 / %62 | 3.417 | 0 |
| 0,60 + STD 0,1/800 | 0,3 | 0 | %83 / %83 | 190 | 0 |

**Okuma:**
- Tamamen kararlı üç ayar var; ayırt edilebilirlikte en iyisi **0,45 + STD** (%96).
- Şeker→MN9 yanıtı yalnızca 0,50 ve üzeri ölçeklerde, ek mekanizma olmadan görülüyor; bu ayarların hepsi kararsız. Hiçbir ayar üç ölçütü aynı anda sağlamıyor.
- Acı→MN9 her ayarda 0. Yanıt görülen her yerde seçicilik korunuyor.
- İstatistik notu: koku doğruluğu 24 örneğe dayanıyor. Bir örnek yaklaşık 4 puan ediyor; birkaç puanlık farklar anlamlı değil.

**Olası neden:** Sinaptik depresyon, 150 Hz'de uyarılan duyu nöronlarının sinapslarını da yoruyor. Kaynak kararlı durumda yaklaşık 1 / (1 + 0,1 × 150 × 0,8) ≈ 0,08'e iniyor ve şeker sinyali daha beyne girerken sönüyor.

## Bulgu 6: Duyu nöronları depresyondan muaf

Duyu nöronlarının Poisson hızı zaten duyu organının etkin çıktısını temsil ediyor. Bu nöronlar girdi almadıkları için yankı döngülerinin parçası da değiller. Bu yüzden `std_skip_sensory` seçeneği eklendi: duyu nöronları (`superclass` içinde "sensory" geçenler) depresyondan muaf tutuluyor.

Yeniden üretmek için: `--grid duyu-muaf` ve `--grid duyu-muaf-yuksek`.

| ayar | MN9 şeker | MN9 acı | koku doğruluk 200 / 500 ms | kalıcı (koku) | kalıcı (tat) |
|---|---|---|---|---|---|
| 0,45 + STD 0,1 | 0 | 0 | %75 / %83 | 0 | 0 |
| 0,45 + STD 0,2 | 0 | 0 | %67 / %75 | 0 | 0 |
| 0,50 + STD 0,1 | 0 | 0 | %79 / %79 | 82 | 0 |
| 0,50 + STD 0,2 | 0 | 0 | %88 / %75 | 0 | 0 |
| 0,55 + STD 0,1 | 0 | 0 | %92 / %96 | 205 | 0 |
| **0,55 + STD 0,2** | 0 | 0 | **%96 / %96** | **0** | **0** |
| 0,60 + STD 0,1 | 2,0 | 0 | %75 / %83 | 192 | 0 |
| 0,60 + STD 0,2 | 0 | 0 | %67 / %71 | 0 | 0 |
| 0,70 + STD 0,1 | 5,7 | 1,0 | %33 / %42 | 239 | 231 |
| **0,70 + STD 0,2** | **3,7** | **0** | %75 / %75 | **0** | **0** |
| 0,70 + STD 0,3 | 0,7 | 0 | %71 / %71 | 665 | 0 |
| 0,80 + STD 0,2 | 4,3 | 0 | %71 / %75 | 272 | 0 |
| 0,80 + STD 0,3 | 3,0 | 0 | %75 / %75 | 415 | 0 |
| 1,00 + STD 0,2 | 6,7 | 1,3 | %46 / %50 | 353 | 153 |
| 1,00 + STD 0,3 | 3,7 | 0 | %46 / %54 | 286 | 0 |

Muafiyet 0,45–0,55 aralığında şeker yanıtını geri getirmedi; yorulma aradaki aktarıcı nöronlarda da etkili. **0,70 + STD 0,2 (duyu muaf)**, üç ölçütü (kararlılık, tat seçiciliği, koku ayırt edilebilirliği) birlikte sağlayan tek ayar.

## Bulgu 7: Finalistlerin sağlamlık testi

16 koku × 6 deneme (şans düzeyi %6,25), tat için 6 deneme. Yeniden üretmek için: `python -m flybrain.experiments.stability --grid finalist --workers 3 --trials 6 --odors 16`

| aday | MN9 şeker (Hz) | MN9 acı (Hz) | koku doğruluk 200 / 500 ms | kalıcı (koku) | kalıcı (tat) |
|---|---|---|---|---|---|
| **A:** 0,45 + STD 0,1/800 | 0 | 0 | %82 / %82 | 0 | 0 |
| **B:** 0,70 + STD 0,2/800, duyu muaf | **3,7** | **0** | %64 / %62 | 0 | 0 |
| **C:** 0,55 + STD 0,2/800, duyu muaf | 0 | 0 | **%89 / %86** | 0 | 0 |

- Üç finalist de 96 koku ve 12 tat denemesinin hiçbirinde kalıcı aktivite üretmedi.
- Kalıcılık olmadığı için beyin durumu postlar arasında sıfırlanmadan taşınabilir. Sinaptik kaynaklar (τ = 800 ms) yakın geçmişin kısa süreli bir izini doğal olarak tutuyor.
- 200 ms'lik pencere, 500 ms kadar bilgi taşıyor. Karar penceresi kısaltılırsa sinek daha hızlı karar verebilir.

## Karar: K-011, beynin çalışma ayarı

**B seçildi:** ağırlık ölçeği 0,70, sinaptik depresyon U = 0,2, τ = 800 ms, duyu nöronları muaf. Kodda `flybrain.sim.BRAIN_PARAMS` olarak tanımlı. Gerekçe için [kararlar.md](kararlar.md#k-011--beynin-çalışma-ayarı) dosyasına bakın.
