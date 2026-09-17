# 09 — Gövde (bedenlenme)

> Durum: **Faz 5 sürüyor (2026-09-17).** Motor nöron → kas → eklem zinciri çalışıyor; hortum ve sıçrama nöronlardan üretiliyor, yürüme henüz koordine değil. Bu belge, sineğin 3D fizik gövdesini kendi motor nöronlarıyla hareket ettirme çalışmasını anlatır. Kararlar: K-019, K-020, K-021, K-022.

## 1. Neden gövde?

Kullanıcının isteği: sineği 3D olarak görmek. Yürüdüğünü, Instagram kullandığını ve korkup kaçtığını izlemek, beyin aktivitesini görmek. Tek şart var: **görünen her hareketi sineğin simüle edilen nöronları üretmeli.** Animasyon, senaryolu hareket ya da sinek yerine karar veren kod olmayacak.

Bu şart iki şey demek:

1. **Gövdede eğitilmiş kontrolcü olmayacak.** Hareketi motor nöron spike'ları üretecek. Hazır yürüme programı, taklit öğrenmesi ya da pekiştirmeli öğrenmeyle eğitilmiş politika kullanılmayacak.
2. **Hareket kusurluysa kusurlu gösterilecek.** Eksikler biyolojik gerekçeli düzeltmelerle giderilecek ve her düzeltme belgelenecek. Görüntüyü güzelleştirmek için davranış eklenmeyecek.

## 2. Mevcut çalışmalar ve farkımız

| Çalışma | Gövde | Beyin–gövde bağlantısı | Bizim için anlamı |
|---|---|---|---|
| NeuroMechFly v2 / FlyGym 2.1 (EPFL, 2024–2026) | Gerçek bir sineğin mikro-BT taramasından 3D model, MuJoCo fiziği | Kullanıcıya bırakılmış; örneklerde hazır ritim üreteçleri ve kayıt tekrarları var | **Gövde olarak kullanıyoruz** (K-019) |
| flybody (Janelia + DeepMind, *Nature* 2025) | Uçabilen ayrıntılı model | Pekiştirmeli öğrenmeyle eğitilmiş sinir ağı | Uçuş kontrolcüsü eğitilmiş, bu yüzden kullanılamaz |
| Eon Systems (Mart 2026) | NeuroMechFly | Shiu beyin modelinden 7–10 inen nöron okunuyor. Bu nöronlar, taklit öğrenmesiyle eğitilmiş kontrolcüleri tetikliyor. Ekip de eşlemelerin çoğunun elle seçildiğini açıkça yazıyor. | Kaçındığımız yol: hareketi beyin değil, eğitilmiş kontrolcü üretiyor |
| Pugliese ve ark. (2025) | Yok | Sinir kordonu konnektomu tek başına, eğitimsiz | Yürüme ritminin konnektomdan çıkabileceğini gösteriyor |

**Farkımız:** Eon'un kullandığı FlyWire verisi yalnızca beyni içeriyordu. Sinir kordonu (omuriliğin sinekteki karşılığı) eksik olduğu için bacak hareketini eğitilmiş kontrolcülere bırakmak zorundaydılar. MaleCNS ise sinir kordonunu, ritim devrelerini ve **sürdükleri kasa göre etiketlenmiş** motor nöronları içeriyor:

| Motor nöron tipi (örnek) | Adet | Kas |
|---|---|---|
| Acc. ti flexor MN, Ti flexor MN | 47 + 37 | Kaval kemiği bükücüleri |
| Tr flexor MN, Tr extensor MN | 35 + 11 | Trokanter bükücü / açıcı |
| Fe reductor MN | 20 | Femur döndürücü |
| Sternal anterior/posterior rotator MN | 12 + 22 | Koksa döndürücüleri |
| Tergotr. MN (TTMn dahil) | 12 | Tergotrokanter: sıçrama kası |
| DLMn, DVMn | 8 + 10 | Dolaylı uçuş kasları |
| MN1–MN12 | 67 (beyin) | Hortum kasları |
| MNad… | 214 | Karın kasları |

Bu sayede zincir doğrudan kurulabiliyor: **motor nöron spike'ları → kas aktivasyonu → eklem torku → fizik.**

## 3. Yürüme ritmi yoklaması (DNg100)

Pugliese ve ark. (2025) sinir kordonunda üç nöronluk bir ritim çekirdeği buldu: E1 (IN17A001), E2 (INXXX466) ve I1 (IN16B036). Yürüme komut nöronu DNg100 uyarılınca bu çekirdek bacak motor nöronlarında 7–15 Hz ritim üretiyor. Bulgu MaleCNS'te de tekrarlanmış ve spike'lı modelle de doğrulanmış. Bu nöronların hepsi bizim konnektomumuzda var (DNg100: 2, çekirdek: 18 nöron).

**Deney:** DNg100 (sol + sağ), 2 sn boyunca Poisson girdiyle uyarıldı; ilk 500 ms atıldı. Beyin ayarı K-011. Sinaptik depresyon muafiyetinin kapsamı değiştirildi. Kod: `python -m flybrain.experiments.walking --hz 50 180`.

| Depresyon muafiyeti | DNg100 | Ritim çekirdeği | Bacak motor nöronları |
|---|---|---|---|
| Yok (K-011) | 50 Hz | sessiz (0/18) | sessiz (0/381) |
| Yok (K-011) | 180 Hz | sessiz (0/18) | sessiz (0/381) |
| Yalnızca DNg100 | 50 Hz | 6,7 Hz, 12/18 aktif | 0,3 Hz, 34/381 aktif, tepe 6,7 Hz |
| Yalnızca DNg100 | 180 Hz | 24,9 Hz, 6/18 | 1,7 Hz, 41/381 |
| Tüm inen nöronlar | 50 Hz | 6,6 Hz, 12/18 | 0,4 Hz, 31/381, tepe 10,7 Hz |
| Tüm inen nöronlar | 180 Hz | 25,6 Hz, 9/18 | 1,9 Hz, 56/381 |
| İnen nöronlar + sinir kordonu | 180 Hz | 27,7 Hz, 15/18 | 4,7 Hz, 73/381 |

**Bulgular:**

- **K-011 ayarında yürüme komutu iletilmiyor.** DNg100'ün her spike'ı E1 nöronlarına 19–32 mV veriyor; bu tek başına E1'i ateşlemeye yeter. Ama U = 0,2, τ = 800 ms'lik depresyon, sürekli ateşleyen bir sinapsın iletimini, ateşleme hızı ne kadar yüksek olursa olsun saniyede en fazla 1/(U·τ) = 6,25 tam spike'a eşdeğer düzeyde tutuyor (kararlı durumda iletim r/(1 + U·r·τ); 180 Hz'de 6,0). Faz 2'de kalıcı çekiciyi önlemek için eklenen mekanizma, sürekli komutları da boğuyor (Z-22).
- **Muafiyetle yol açılıyor.** Ritim çekirdeği ve 30–70 bacak motor nöronu ateşliyor. Baskın frekans bazen yürüme bandında (6,7 ve 10,7 Hz), bazen üstünde (21–25 Hz).
- **Ritim zayıf.** Tepe frekansın güç payı 0,06–0,10. 2–40 Hz bandı yaklaşık 57 frekans kutusu olduğundan düzensiz bir dizide bu pay yaklaşık 0,018 olurdu; ölçülen değer bunun 3–5 katı.
- **Ölçüm bükücü ve açıcı kasları topluyor.** Bu iki grup zıt fazda çalıştığı için toplamda ritim kısmen sönüyor olabilir. Sonraki adımda ritim kas grubu başına ölçülecek.
- **Beklenen bir eksik:** Pugliese ve ark. da bacaklar arası koordinasyonun (tripod yürüyüş) gövdeden gelen his olmadan ortaya çıkmadığını bildiriyor. Bu yüzden propriyosepsiyon bu fazın bir parçası (Z-23).

## 4. FlyGym gövdesi: ilk yoklama

FlyGym 2.1.0 kuruldu (Apache-2.0; MuJoCo 3.9). Varsayılan sadeleştirilmiş 3D modeller paketle geliyor. Yüksek çözünürlüklü modeller EPFL'in genel deposundan yalnızca istenirse iniyor; şimdilik kullanılmıyor.

**Eklemler** (`JointPreset.ALL_BIOLOGICAL`): toplam 126 serbestlik derecesi.

| Bölge | Serbestlik derecesi |
|---|---|
| Bacaklar: koksa 18, trokanter-femur 12, tibia 6, tarsus 30 | 66 |
| Baş | 3 |
| Hortum: rostrum 3, haustellum 3 | 6 |
| Kanatlar | 6 |
| Halterler (denge organı) | 6 |
| Karın (5 segment) | 15 |
| Antenler (pedicel, funiculus, arista) | 18 |
| Gözler | 6 |

**Ölçümler:**

- **Hız:** Tüm eklemlere tork aktüatörü takılı ve zaman adımı 0,1 ms iken fizik, gerçek zamanın **1,3 katı hızında** çalışıyor. Bu ölçüme görme ve çizim dahil değil.
- **Pasif duruş:** FlyGym'in varsayılan eklem sertliğiyle (10) sinek motor girdisi olmadan dimdik duruyor (göğüs 0,73 mm). Kas modelinin sertliğiyle (0,4) çömeliyor ama yere yapışmıyor (0,46–0,68 mm). Gerçek sinekte duruşu yavaş motor nöronların tonik ateşlemesi sağlar; bizim modelde dinlenen beyin sessiz (Z-29).
- **Görme:** Bileşik göz her göz için 721 ommatidyum veriyor. İlk çağrı 2,6 sn sürdü (hazırlık dahil); sonraki çağrıların maliyeti ayrıca ölçülecek.

## 5. Plan

### 5.1 Motor nöron → kas → eklem

- **Eşleme tablosu:** Her motor nöron tipi, sürdüğü kas üzerinden bir eklem serbestlik derecesine ve yöne bağlanır (ör. Ti flexor → tibia pitch, bükme yönü). Tablo anatomi literatürüne dayanır ve kaynaklarıyla belgelenir. Davranışa bakılarak ayarlanmaz.
- **Kas aktivasyonu:** Spike dizisinin kas seğirmesi süresinde süzülmüş hali.
- **Tork:** Kuvvet ölçeği, kas fizyolojisinden ve eklemin pasif sertliğinden türetilir.
- **Gövde bölgeleri:**
  - bacaklar
  - baş (boyun motor nöronları)
  - hortum (MN1–12)
  - kanatlar (yönlendirme kasları; kur şarkısı için uçuş kasları)
  - karın
  - sıçrama (TTMn)

### 5.2 Gövdeden beyne his (propriyosepsiyon)

- **Kaynaklar ve ilgili duyu nöronları:**
  - eklem açısı ve hızı: femoral kordotonal organ, kıl plakaları
  - yük: kampaniform sensiller
  - zemin teması: tarsal kıllar
  - baş konumu: boyun kıl plakaları
- **Kodlama:** Gövdeden gelen bu işaretler Poisson hızlarına çevrilip konnektomdaki karşılık gelen duyu nöronlarına verilir.

### 5.3 Kapalı döngü

- **Adım eşleşmesi:** Beyin ve fizik aynı 0,1 ms adımla çalışıyor. Aralarında birkaç milisaniyede bir veri alışverişi yapılır: spike'lar kaslara gider, gövde durumu duyulara döner.
- **Görme:** Sineğin gözleri, önündeki ekranı sahnenin içinde görür. Ommatidyumlar, Faz 3'teki kolon eşlemesiyle konnektomun göz kolonlarına bağlanır.

### 5.4 Sahne (K-021)

- **Düzen:** Serbest sinek; Instagram ekranı sineği izleyen bir sanal gerçeklik yüzeyi (FreemoVR düzeninin benzeri).
- **Kaçış:** Sinek gerçekten sıçrayıp uzaklaşabilir; ekran onu izlemeye devam eder, yeniden yerleştirme gerekmez.
- **İnsan kararı:** Bu düzen "dünyanın fiziği" kategorisindedir ve belgelenir.

### 5.5 Nöral karar ile görünen hareketin tutarlılığı (K-020)

Instagram eylemleri Faz 4'teki kas grubu okumasıyla seçilmeye devam ediyor. Gövde aynı motor nöronlarla hareket ettiği için ikisi aynı kaynaktan geliyor, ama örtüşme ölçülerek güvenceye alınacak:

- **Ölçüt:** Her kararın kanalına karşılık gelen gövde bölgesi (hortum, bacaklar, karın, kanat, baş), o pencerede taban düzeyinin üstünde hareket etmiş olmalı.
- **Açık sorular (Z-27):**
  - "İlgi kaybı" ile kaydırmada görünen bir hareket yok.
  - İleri kanalı gerçek yürüme olmadan da eşiği aşabilir.

### 5.6 Bitiş kriterleri (Faz 5)

- [x] Beyin sessizken gövde pasif duruşta kalıyor
- [x] MN9 uyarımı → hortum uzuyor
- [ ] Şeker tadı → MN9 → hortum uzuyor (uçtan uca): kısmen, bkz. 6.4
- [x] Dev lif (DNp01) uyarımı → TTMn → orta bacaklar açılıyor → sinek sıçrıyor
- [ ] DNg100 uyarımı → bacaklarda ritmik hareket (ne kadar yürüdüğü ölçülüp raporlanır)
- [x] Bacak hareketi → propriyoseptif duyu nöronları ateşliyor (bkz. 7)
- [ ] Nöral kararlar ile gövde hareketinin örtüşmesi ölçülüyor
- [x] Sinek sahneyi kendi gözleriyle görüyor (bkz. 9)
- [ ] Kapalı döngü (beyin + gövde + görme) gerçek zamanın en fazla 3 katı yavaşlıkta: şu an ~5 kat (bkz. 9.3)

## 6. İlk uygulama (2026-09-17)

Kod: `flybrain/body/` (`derive.py`, `muscles.py`, `body.py`, `embodied.py`), deneyler: `python -m flybrain.experiments.body`, testler: `tests/test_body.py`.

### 6.1 Kas geometrisi nereden geliyor?

FlyGym'in içinde, FlyMimic çalışmasının sol ön bacak kas-iskelet modeli var. Model X-ray tomografisinden 15 kas içeriyor ve **kas adları konnektomdaki motor nöron tipleriyle birebir aynı** (tergopleural promotor, sternal adductor, trokanter bükücü, tibia açıcı...). `derive.py` bu modelden şunları okuyup `muscle_geometry.json` dosyasına yazıyor:

- **Moment kolları:** Her kasın her eklemdeki kolu (tendon uzunluğunun açıya göre türevi, nötr pozda). Tendonlar düz çizgi olduğu için 3D modellere gerek yok, ek indirme yapılmadı.
- **Kuvvetler:** En büyük kuvvetler (F0), kas kesit alanından tahmin edilmiş. Birim µN.
- **Pasif özellikler ve sınırlar:** Eklemlerin sertlik ve sönüm değerleri (0,4 µN·mm/rad ve 0,02) ve anatomik açı aralıkları.
- **Karşıt kaslar kontrol edildi:** Her eklemde ters yönde çekiyorlar. Örneğin tibia bükücüsü açıyı artırıyor, açıcısı azaltıyor.

Kas-iskelet modeli ile NeuroMechFly aynı eklem düzenini kullanıyor; eksenler ve nötr açılar örtüşüyor. Bu yüzden kollar eklem uzayında doğrudan aktarılıyor.

Diğer yönler, NeuroMechFly'ın nötr pozunda küçük açı değişimlerinin gövde parçalarını nereye taşıdığına bakılarak **geometriden** belirleniyor:

| Hareket | Eklem | Yöntem |
|---|---|---|
| Hortum ileri (rostrum) | `c_head-c_rostrum-pitch`, − yön | haustellum öne gidiyor |
| Haustellum açılma | `c_rostrum-c_haustellum-pitch`, + yön | uç, tabandan uzaklaşıyor |
| Baş sola dönme | `c_thorax-c_head-roll`, + yön | ekseni dikey olan serbestlik derecesi |
| Kanat açma | `c_thorax-*_wing-roll`, − yön | kanat en çok yana gidiyor |
| Karın aşağı bükme | 5 segmentte `pitch`, − yön | uç segment aşağı iniyor |
| Tibia bükme | `*_tibia-pitch`, + yön (6 bacak) | tarsus femur tabanına yaklaşıyor |
| Tarsus aşağı bükme | tibia ile aynı yön | eksenler paralel; nötr pozda tarsus neredeyse düz olduğu için mesafe ölçütü kullanılamıyor |

**Sıçrama kası (TTM):** Zumstein ve ark. (2004) orta bacağın ucunda 101 µN tepe kuvvet ve 8,2 ms yükselme süresi ölçmüş. Bu kuvvet, orta bacağın 1,48 mm'lik kaldıraç koluyla 149 µN·mm torka çevriliyor.

### 6.2 Kas tablosu

- **Eşlenenler:** 105 kas, 701 motor nöron.
  - bacak kasları (6 bacak)
  - TTM
  - hortum (McKellar ve ark. 2020)
  - boyun
  - kanat yönlendirme kasları
  - karın
- **Eşlenmeyenler (191 nöron):**

| Grup | Neden |
|---|---|
| Uçuş güç kasları (DLMn, DVMn) | Uçuş modellenmiyor (Z-26) |
| Femur döndürücü (Fe reductor, 20) | Kas-iskelet modelinde yok |
| Labellum ve yutak kasları (MN5–8, MN10–13, CEM) | Gövde modelinde bu parçalar yok |
| Halter, anten ve retina kasları | Henüz eşlenmedi |
| Adsız tipler (MNml…, MNhl…, MNx…) | İşlevleri bilinmiyor |

### 6.3 Kas modeli

- **Seğirme:** Her motor nöron spike'ı nöronun seğirme durumunu Δ·(1−x) kadar artırır (Δ = 0,3; TTM tek seğirmeli kas olduğu için Δ = 1). Durum 40 ms'de söner.
- **Kuvvet:** Kasın uyarılması, sürdüğü motor nöronların ortalamasıdır. Kuvvet bu uyarılmayı 8,2 ms gecikmeyle izler.
- **Boy–kuvvet:** Bir kas tamamen kısaldığında kuvvet üretemez. Sınırlı eklemlerde, eklem kasın çektiği yöndeki sınıra yaklaştıkça (aralığın son %25'i) tork sıfıra iner. Bu olmadan, sıçramadan sonra havadaki orta bacaklar eklem sınırını aşıp 90 rad döndü.
- **Eklem sınırları:** Tepki süresi 20 ms'den 0,5 ms'ye indirildi; varsayılan yumuşak sınır, kas torkları karşısında aşılıyordu.
- **Oturma:** Gövde nötr pozdan pasif duruşuna 500 ms'de oturuyor. Her deney bu oturmadan sonra başlıyor.
- **Beyin–gövde eşleşmesi:** Her 1 ms'de bir. Parçalamanın beyin simülasyonuna ek maliyeti yok (ölçüldü).

### 6.4 Neden–sonuç deneyleri

Her deney 500 ms oturma ve 300 ms sessiz başlangıçla başlıyor. Videolar `runs/body-*.mp4`; üç deneyin yan yana hali: `python -m flybrain.experiments.body --montage`.

| Deney | Motor nöron spike'ı | Gövde |
|---|---|---|
| Sessiz beyin (1 sn) | 0 | Hiçbir eklem kıpırdamıyor, göğüs 0,68 mm yükseklikte duruyor ✅ |
| MN9, 150 Hz, 600 ms | hortum 154 | Rostrum 0,69 rad ileri, haustellum 0,69 rad açılıyor ✅ |
| Şeker tadı (LB3b/c), 800 ms | hortum 12, boyun 18, bacak 4 | Haustellum 0,32 rad açılıyor ama rostrum ileri gitmiyor. En çok çalışanlar: MN4b (haustellum açıcı), MN2Da (**geri çekici**), MN9. Tam hortum uzatma (PER) yok (Z-30) |
| Dev lif, 300 Hz, 15 ms | TTMn 2 + 1 | Orta bacaklar 1,6 rad açılıyor. Göğüs 1,2 mm yükseliyor, sinek 3,3 mm öteye sıçrıyor, en fazla 51° yalpalıyor ✅ |
| TTMn doğrudan | TTMn 2 | Aynı sıçrama (kas ve fizik kontrolü) ✅ |
| DNg100, 150 Hz, 1,5 sn (inen nöronlar depresyondan muaf) | bacak 1.112, boyun 139, karın 65, kanat 25 | Bacaklar kıpırdıyor: 0,73 mm yol ama net 0,15 mm, en fazla 9° yalpalama. **Yürüme yok**, koordinasyon yok (Z-23) |

**Dev lif için elektriksel sinaps (K-023):** Konnektomda dev liften TTMn'ye kimyasal sinaps var (sağ 70, sol 20). Ama tek bir dev lif spike'ının TTMn'de yarattığı tepe gerilim 2 mV civarında, eşik farkı ise 7 mV. Depresyon da sürekli ateşlemede iletimi boğuyor (150 ms'lik uyarımda bile TTMn hiç ateşlemedi). Gerçek sinekte bu bağlantı elektriksel sinapsla 1:1 çalışıyor ve elektriksel sinapslar elektron mikroskobu konnektomunda görünmüyor. Ölçülmüş bu bağlantı, 1:1 iletimi sağlayan ağırlıkla modele eklendi (`flybrain/connectome/electrical.py`). Bu eklemeden sonra 15 ms'lik darbe sıçramayı tetikliyor.

**Önceki denemeden bir not:** Oturma adımı eklenmeden önce sıçrama, sinek henüz yere oturmamışken tetikleniyordu ve sinek havada takla atıp sırtüstü düşüyordu. Sırtüstü kalan sinek doğrulamıyor, çünkü motor nöronları sessiz (Z-26).

### 6.5 Varsayımlar (kaynağı olmayan parametreler)

| Parametre | Değer | Etkisi |
|---|---|---|
| Seğirme artışı Δ | 0,3 (TTM 1,0) | Hareketin şiddeti |
| Gevşeme süresi | 40 ms | Hareketin süresi |
| Yükselme süresi (TTM dışı kaslar) | 8,2 ms (TTM ölçümü) | Hareketin hızı |
| Boy–kuvvet kenarı | aralığın %25'i | Sınıra yakın tork |
| Orta ve arka bacaklar | Ön bacağın kas geometrisi ve aralıkları, nötr açıya göre kaydırılarak | Bacakların yapısal benzerliği varsayımı |
| Tarsus aralığı ve kas torku | ±0,6 rad; sertlik × 0,5 rad | Tarsus hareketi |
| Hortum, baş, kanat, karın torku | sertlik × açı (1,0 / 0,35 / 1,2 / segment başına 0,15 rad) | Bu bölgelerin hareket genliği |
| Boyun | Her taraftaki boyun motor nöronları başı kendi tarafına çevirir | Baş dönme yönü |
| Kanat | Üçüncü aksiller kaslar kanadı katlar, diğer yönlendirme kasları açar | Kanat açma |
| Karın | Tüm karın motor nöronları aşağı büker; iki taraf arasındaki fark yana büker | Karın hareketi |
| Kas içi paylaşım | Bir kası süren motor nöronlar eşit ağırlıkta | Boyut ilkesi (küçük nöron küçük kuvvet) yok sayılıyor |

Bu değerler hareketin **biçimini ve genliğini** etkiler; **ne zaman** hareket edileceğini her zaman motor nöron spike'ları belirler.

### 6.6 Sıradaki adımlar

1. ~~**Gövdeden beyne his (Z-23)**~~: ilk sürüm tamamlandı, bkz. 7.
2. **Sineğin gözleriyle görme:** Ommatidyumları konnektom göz kolonlarına bağlamak.
3. **Sahne:** Sineği izleyen Instagram ekranı.
4. **Kapalı döngü hızı:**
   - Sessiz beyinle 1 sn simülasyon: videosuz yaklaşık 3 sn, iki kameralı kayıtla 6 sn.
   - Hedef: gerçek zamanın en fazla 3 katı.
5. **Nöral karar ile gövde tutarlılığı (Z-27):**
   - Faz 4 okumasında TTMn ve STTMm (sıçrama kasları) "yorum" kanalında sayılıyor; "çıkış" kanalına taşınmalı.
   - Bu değişiklik yeniden kalibrasyon gerektiriyor.

## 7. Propriyosepsiyon (2026-09-17)

Gövdenin eklem açıları ve açısal hızları her milisaniyede konnektomdaki bacak propriyoseptörlerinin Poisson hızlarına çevriliyor (`flybrain/body/proprio.py`). Beyin bu nöronları, dışarıdan verilen duyusal uyarımla birlikte alıyor. Karar: K-024.

### 7.1 Hangi nöronlar, neyi algılıyor?

- **Bacak ataması:** Duyu nöronlarının hücre gövdesi beyin dışında olduğundan bacak, sinir kordonuna girdiği sinirden (`entryNerve`) okunuyor:
  - ön bacak: ProLN, ProAN, VProN, DProN
  - orta bacak: MesoLN
  - arka bacak: MetaLN
  - Taraf kökten (`rootSide`) geliyor.
- **Uyluk kordotonal organı (FeCO):** Femur–tibia eklemini izliyor. MaleCNS eşanlamlıları pençe (claw), kanca (hook) ve topuz (club) tiplerini veriyor, ama pençe ve kancanın bükülmeye mi açılmaya mı duyarlı olduğunu vermiyor.
  - **Çözüm:** Lee ve ark. (2025) FANC konnektomunda bir bağlantı imzası bildiriyor. Bükülme algılayıcıları tibia açıcı motor nöronlarına doğrudan uyarıcı, bükücülere dolaylı ketleyici geri bildirim veriyor; açılma algılayıcıları tersini yapıyor. Bu imza MaleCNS'te her tip için ölçüldü (`python -m flybrain.experiments.proprio`, tüm bacakların toplamı, sinaps sayısı):

| Tip | Doğrudan → açıcı | Doğrudan → bükücü | İki adım → açıcı | İki adım → bükücü | Atama |
|---|---|---|---|---|---|
| SNpp50 (pençe) | 408 | 49 | +74 | −374 | bükülme |
| SNpp51 (pençe) | 0 | 329 | −149 | +137 | açılma |
| SNpp41 (kanca) | 88 | 0 | +44 | −29 | bükülme |
| SNpp39 (kanca) | 0 | 419 | −20 | +104 | açılma |

  "İki adım": duyu nöronu → ara nöron → motor nöron etkisi. Ara nöronun girdisindeki payla ağırlıklandırıldı ve işaretli.

  Dört tipin dördü de imzaya net biçimde uyuyor. Topuz tipleri (SNpp40, 47, 56, 57, 60) iki yönlü hareket algılayıcısı; yön ataması gerekmiyor.

- **Kıl plakaları (SNpp45, SNpp52):** Eklem sınırı dedektörleri (Pratt ve ark. 2026). CxHP8 plakası bacağın öne hareketinin sınırında ateşliyor ve bacağı geri götüren kasları uyarıyor.
  - **Genelleme (VARSAYIM):** Bu düzen tüm plakalara uygulandı. Her plaka grubu için doğrudan uyardığı kasların eklem torkları toplanıyor; en büyük payı alan eklem, plakanın izlediği eklem sayılıyor. Plaka, kasların hareket yönünün tersindeki sınırda ateşliyor.
  - **Sonuç:**
    - SNpp45 her bacakta koksa roll ekleminde.
    - SNpp52 orta ve arka sol bacaklarda ve sağ arka bacakta trokanter pitch ekleminde, diğerlerinde koksa roll ekleminde. Bu tutarsızlık, tip içinde birden fazla plaka olabileceğini düşündürüyor.
- **Dışarıda kalanlar:**
  - **Yük algılayıcıları (kampaniform sensiller):** Bacaklarda yalnızca 13 nöron bu etiketi taşıyor (SNpp53); gerçek sinekte bacak başına onlarca var.
  - **Tarsal temas:** Dokunma kıllarının bacağın neresinde olduğu etiketlerde yok.
  - **Diğer tipler:** Yönü belirsiz kordotonal tipler (SNpp42–44, 46, 48, 49, 58, 59) ve adı olmayan bacak propriyoseptörleri (SNppxx, 78 nöron).
  - **Boyun kıl plakaları (SNpp19):** Boyun motor nöronlarına doğrudan ve dolaylı etkileri zıt yönde; boyun kas modeli de zaten bir varsayım.

| Grup | lf | lm | lh | rf | rm | rh | Toplam |
|---|---|---|---|---|---|---|---|
| Pençe, bükülme | 1 | 14 | 18 | 0 | 12 | 17 | 62 |
| Pençe, açılma | 3 | 9 | 5 | 1 | 6 | 8 | 32 |
| Kanca, bükülme | 1 | 3 | 3 | 2 | 8 | 5 | 22 |
| Kanca, açılma | 3 | 8 | 7 | 5 | 9 | 7 | 39 |
| Topuz | 9 | 31 | 32 | 4 | 31 | 31 | 138 |
| Kıl plakası | 11 | 22 | 14 | 8 | 22 | 19 | 96 |

Toplam 62 grup, 389 nöron.

**Veri eksiği:** Ön bacakların FeCO'su MaleCNS'te çok eksik (sol ön bacakta 1, sağ ön bacakta 0 bükülme pençesi). FANC'ta tek bir ön bacakta 58 pençe ve kanca aksonu var. ProLN'den giren 185 duyu nöronu tipsiz ve modalitesi bilinmiyor.

### 7.2 Kodlama

| Kodlama | Kullanan | Hız |
|---|---|---|
| Pozisyon (tonik) | pençe, kıl plakası | R_max · σ((yön·açı − eşik) / genişlik) |
| Hız (fazik, yönlü) | kanca | R_max · kırp((yön·ω − eşik) / 5 rad/s) |
| Sürat (fazik, iki yönlü) | topuz | R_max · kırp((\|ω\| − eşik) / 5 rad/s) |

- **Aralık bölüşümü:** Bir gruptaki nöronların eşikleri aralığa eşit yayılıyor. Böylece açı arttıkça daha çok nöron devreye giriyor (Mamiya ve ark. 2018/2023).
  - **Pençe:** Bükülme pençeleri femur–tibia iç açısı 90°'nin altını, açılma pençeleri üstünü kodluyor (Agrawal ve ark. 2020). Eşikler 90°'den eklem sınırına kadar yayılıyor.
  - **Kıl plakaları:** Aralığın son %30'unu kodluyor.
- **Açı kuralı:** Modelde tibia açısı 0 iken bacak düz (iç açı 180°) olduğu doğrulandı. İç açı = 180° − bükülme.
- **Oturma:** Propriyosepsiyon oturma sırasında kapalı. Model sineği havada nötr pozda başlatıyor ve bu yapay iniş beyne iletilmiyor.

### 7.3 Deneyler

**Sessiz beyin, propriyosepsiyon açık (1 sn):**
- Nötr pozda 31 propriyoseptör ateşliyor (toplam ~1.200 Hz).
- Bacak motor nöronlarında 18 spike var ve beyin kaçak aktiviteye girmiyor.
- Göğüs 0,68 yerine 0,64 mm'de, en fazla 3,8° yalpalama.

**Direnç refleksi:** Tibia, deneycinin probu gibi bir dış torkla 0,5 rad bükülüyor ya da açılıyor (400 ms). Prob, `Body.apply_external` ile yalnızca deneyde uygulanıyor.

| Bacak | Bükme: açıcı MN (spike/s) | Açma: bükücü MN (spike/s) |
|---|---|---|
| lm | 3,3 → 10,0 | 3,3 → 0 (açıcı da 3,3 → 0) |
| rh | 0 → 2,5 | 13,3 → 15,0 |
| Diğer dört bacak | 0 → 0 | 0 → 0 |
| Propriyosepsiyon kapalı (tüm bacaklar) | 0 → 0 | 0 → 0 |

- **Yön doğru:** Görüldüğü her durumda bükme açıcıyı, açma bükücüyü çalıştırıyor. Ters yönde bir tepki hiç yok.
- **Genlik zayıf:** Refleks çoğu bacakta eşiğin altında kalıyor (Z-31).

**Önceki deneyler, propriyosepsiyon açık:**

| Deney | Propriyosepsiyon kapalı | Açık |
|---|---|---|
| MN9 | hortum 0,69 rad | aynı |
| Şeker | haustellum 0,32 rad | 0,12 rad |
| Dev lif | TTMn 3 spike; 1,9 mm yükseklik; 51° | TTMn 12 spike (5'i uyarım bittikten sonra); 3,1 mm; 78° |
| DNg100 | bacak 1.112 spike; yürüme yok | bacak 1.578 spike; **TTMn 3 spike → sıçramaya benzer hareket**; yürüme yok |

- **Sıçramadan sonraki ek TTMn spike'ları:** Konnektomdaki bir yoldan geliyor. Propriyoseptörler, uyarıcı ara nöronlar (IN20A.22A001, GFC2, IN20A.22A003) üzerinden TTMn'ye ulaşıyor; ketleyici yollar da var (IN13A022, IN13A032).
- **DNg100 sırasındaki TTMn ateşlemesi:** Aynı yoldan geliyor ve rastgele tohuma bağlı; aynı koşulun başka bir koşusunda görülmedi. Yürüme komutu altında sıçrama kası ateşlemesi Z-27 açısından izlenecek.

### 7.4 Yürüme neden çıkmıyor? Sinir kordonunun kazancı

DNg100 uyarımı (150 Hz, 1,5 sn) altında bacak motor nöronlarının ortalama hızı (310 bacak motor nöronu):

| Sinaps ağırlığı | Depresyondan muaf | Propriyo | Ort. hız | Aktif MN | TTMn | Yol / net | En büyük eğim |
|---|---|---|---|---|---|---|---|
| ×0,70 (K-011) | inen | kapalı | 1,6 Hz | 60 | 0 | 0,43 / 0,11 mm | 6° |
| ×0,70 | inen | açık | 2,1 Hz | 65 | 0 | 0,52 / 0,16 mm | 9° |
| ×0,70 | inen + sinir kordonu | kapalı | 3,5 Hz | 61 | 0 | 0,67 / 0,13 mm | 7° |
| ×0,70 | inen + sinir kordonu | açık | 3,4 Hz | 78 | 0 | 1,33 / 0,11 mm | 32° |
| ×0,85 | inen | açık | 3,2 Hz | 84 | 1 | 0,95 / 0,22 mm | 12° |
| ×0,85 | inen + sinir kordonu | açık | 4,3 Hz | 88 | 11 | 7,43 / 0,85 mm | 59° |
| ×1,00 (Shiu) | inen | açık | 7,8 Hz | 116 | 36 | 2,33 / 0,49 mm | 16° |
| ×1,00 | inen + sinir kordonu | açık | 4,9 Hz | 101 | 19 | 4,07 / 0,47 mm | 33° |

- **Hızlar düşük:** Hiçbir ayarda bacak motor nöronları yürümede beklenen onlarca Hz'e çıkmıyor.
- **Kazanç artınca:** Koordinasyon gelmiyor; sıçrama kası tekrar tekrar ateşliyor ve sinek savruluyor.
- **Karşılaştırma:** Pugliese ve ark. (2025) ritmi LIF ile değil, nöron boyutuna göre ölçeklenmiş kazanç ve eşikli, 200 Hz'de doyan hız tabanlı bir modelle elde etti. O modelde de tek bacak içinde ritim çıktı, bacaklar arası koordinasyon çıkmadı.
- **Sonuç:** Mevcut LIF ayarında yürüme için eksik olan yalnızca propriyosepsiyon değil. Sinir kordonunun dinamiği de (kazanç, doyum, nöron boyutu) modellenmeli. Kullanıcı hız modelini seçti (bölüm 8, K-025).

### 7.5 Varsayımlar

| Parametre | Değer | Dayanak |
|---|---|---|
| En yüksek hız | 100 Hz | Ergin sinekte ölçüm yok; larva kordotonal nöronlarında 1,5–78 Hz (Warren ve Göpfert 2024) |
| Pençe ayrımı | iç açı 90° | Agrawal ve ark. 2020 (bükülmüş 0–90°, açılmış 90–180°) |
| Kanca eşikleri | 0,5–10 rad/s, genişlik 5 rad/s | Kaynak yok |
| Topuz eşikleri | 0,2–10 rad/s, genişlik 5 rad/s | Kaynak yok; titreşim duyarlılığı modellenmiyor |
| Kıl plakası bölgesi | aralığın son %30'u | Kaynak yok |
| Kıl plakası yönü | uyardığı kasların tersindeki sınır | CxHP8'de ölçülen düzenin genellemesi |
| Eşiklerin nöronlara dağılımı | bodyId sırasıyla | Hangi nöronun hangi açıya duyarlı olduğu bilinmiyor |

## 8. Sinir kordonu hız modeli (2026-09-17)

Karar: K-025 (kullanıcı: "Sinir kordonu hıza dayalı model"). Durum: **deneysel**; varsayılan model şimdilik tamamen LIF (`EmbodiedFly(vnc="lif")`), hız modeli `vnc="rate"` ile açılıyor.

### 8.1 Yöntem

- **Model (Pugliese ve ark. 2025):**

  τ dR/dt = max(Rmax · tanh(a/Rmax · (I + Σ w R − θ)), 0) − R

  - w = 0,03 × işaretli sinaps sayısı
  - a = a′/s, θ = θ′·s; s = nöron boyutu / ağın medyan boyutu
  - τ′ 20 ± 2 ms, a′ 1 ± 0,1, θ′ 7,5 ± 0,6, Rmax 200 ± 10 Hz; nöron başına kesik normal

  Yazarların kodu (MIT lisanslı) kopyalanmadı. Model makaleden yeniden yazıldı (`flybrain/sim/rate.py`, numba, Euler 0,1 ms). Salınım skoru yazarların tanımıyla hesaplanıyor.
- **Nöron boyutu:**
  - MaleCNS'in açık düz dosyalarında hacim yok. Hacim neuPrint girdi tablosunda (`Neuprint_Neurons.feather`, 4,6 GB).
  - Arrow dosyası HTTP aralık istekleriyle açıldı; yalnızca gövde kimliği ve boyut sütunları, izlenmiş nöronların bulunduğu ilk 6 parçadan okundu (3,8 MB, kullanıcı izniyle; `connectome/sizes.py`).
  - Kapsam: nöronların %98,8'i. Yazarların tablosuyla ortak nöronların %99,3'ünde değer birebir aynı.
  - Eksik boyutlar için aynı tipin, o da yoksa aynı süper sınıfın medyanı kullanılıyor.
- **Yazarların ayarı:** MaleCNS koşusunun yapılandırması, Zenodo'daki 846 MB'lık zip'in yalnızca dizininden ve küçük yaml dosyasından okundu (67 KB). Sağ DNg100'e I = 400, süre 2 sn.
- **Ağ seçimi (yazarların ölçütü):**
  - motor nöronlar,
  - onlara en az bir sinaps yapan nöronlar (nörotransmitter tahmini olanlar),
  - bunlara sinaps yapan inen nöronlar;
  - ağırlıklarda 5 sinaps eşiği.

  Bu ölçüt yazarların ön bacak tablosunun 4.309 nöronunun tamamını buluyor (`connectome/motor_network.py`).

### 8.2 Ön bacak ritminin yeniden üretimi

`python -m flybrain.experiments.vnc_rhythm` (yazarların tablosundaki ağ, bizim bağlantılarımız):

| Koşul | Koşu | Salınan (skor ≥ 0,5) | Skor medyanı | Frekans medyanı | Etkin motor nöron |
|---|---|---|---|---|---|
| Gerçek boyut, dt 0,1 ms | 48 | %97,9 | 0,99 | 11,2 Hz | 8 |
| Sinaps sayısı vekili, dt 0,1 ms | 48 | %0 | 0 | — | 0 |
| Gerçek boyut, dt 0,025 ms | 12 | %91,7 | 0,98 | 11,5 Hz | 8 |

- **Ritim yeniden üretildi.** Frekans, gerçek yürümedeki 7–15 Hz aralığında.
- **Faz farkı:** Kalçayı öne ve arkaya iten motor nöronlar arasında −60° ile −95° arası.
- **Az motor nöron etkin:** Yazarların MaleCNS grafiği de az sayıda etkin motor nöron gösteriyor.
- **Sinaps sayısı vekili işe yaramıyor:** Gerçek boyutla sıra korelasyonu 0,925 olmasına rağmen ritim tamamen kayboluyor. Vekil, inen nöronları ve ritim çekirdeğini ~2 kat büyük, motor nöronları ~2 kat küçük gösteriyor.
- **Adım:** 0,1 ms yeterli.

### 8.3 Ölçeği büyütmek: altı bacak ve tüm kordon

**Tüm kordon (kanat, halter, karın, boyun ağları dahil):**
- DNg100 12 Hz'in altında neredeyse sessiz.
- Üstünde ~7.800 nöronun doyumda ateşlediği, kendini sürdüren bir duruma geçiyor. Bu durumda DNg100 bile ağ tarafından susturuluyor.
- Normalizasyonu değiştirmek geçişin yerini kaydırıyor ama ara bir rejim bırakmıyor.
- Yazarlar da 1.500'den fazla nöronun devreye girdiği koşuları kararsız sayıyor.

**Altı bacağın motor ağı:** 381 motor nöron, 7.946 dinamik ara/çıkan nöron. İnen nöronlar kelepçeli, DNg100 pürüzsüz hızla, 8 tohum (`--bacaklar`):

| DNg100 | Etkin nöron (medyan) | lf | rf | lm | rm | lh | rh |
|---|---|---|---|---|---|---|---|
| 10 Hz | 106 | 0/0 | 0/0 | 6/0 | 0/0 | 8/6 | 8/2 |
| 12 Hz | 266 | 1/1 | 0/0 | 8/6 | 4/4 | 8/8 | 8/8 |
| 14 Hz | 412 | 8/8 | 0/0 | 8/7 | 7/7 | 8/8 | 8/8 |
| 17 Hz | 644 | 8/8 | 8/6 | 8/8 | 8/5 | 8/2 | 8/4 |
| 20 Hz | 853 | 8/8 | 8/8 | 8/8 | 8/7 | 8/2 | 8/2 |
| 25 Hz | 1.123 | 8/8 | 8/8 | 8/2 | 8/1 | 8/1 | 8/0 |

Hücreler: etkin motor nöronu olan tohum / salınan tohum (8'den).

- **Ritim rejimi:** 14–20 Hz'de bacakların çoğu güvenilir biçimde ~10 Hz'de salınıyor.
- **Motor çıktı düşük:** Bacak başına 2–20 motor nöron etkin (bacak başına ~60 var) ve en yüksek hızları 2–38 Hz.
- **Sonuç:** Kanat, karın ve boyun devreleri LIF'te kaldı.

### 8.4 Melez: LIF beyin + hız modeli bacak ağı

`sim/hybrid.py`:
- **LIF → hız ağı:** Hız ağına sinaps yapan LIF nöronlarının (çoğu inen nöron) spike'ları süzülüp kelepçeli hız olarak giriyor.
- **Hız ağı → LIF:** LIF'e sinaps yapan hız ağı nöronları, LIF'te kendi hızlarında Poisson ateşliyor.
- **Motor nöronlar:** Spike sayıları hızlarından Poisson olarak örnekleniyor.

DNg100 17 Hz, 2 sn (`--hibrit`):

| DNg100 girdisi | Ağda etkin | lf | rf | lm | rm | lh | rh |
|---|---|---|---|---|---|---|---|
| Pürüzsüz 17 Hz | 525 | 6 / 0,82 | 3 / 0,18 | 10 / 0,86 | 7 / 0,61 | 18 / 0,44 | 17 / 0,41 |
| Spike, süzgeç 20 ms | 2.009 | 50 / 0,03 | 31 / 0,07 | 27 / 0,00 | 36 / 0,03 | 34 / 0,04 | 35 / 0,08 |
| Spike, süzgeç 100 ms | 2.215 | 49 / 0,01 | 29 / 0,01 | 29 / 0,00 | 33 / 0,00 | 39 / 0,01 | 41 / 0,03 |
| Spike, süzgeç 300 ms | 523 | 8 / 0,14 | 6 / 0,18 | 14 / 0,20 | 12 / 0,13 | 21 / 0,23 | 21 / 0,26 |
| Spike, süzgeç 1000 ms | 350 | 6 / 0,06 | 0 / 0 | 10 / 0,12 | 2 / 0 | 18 / 0,05 | 14 / 0,18 |

Hücreler: etkin motor nöron / salınım skoru.

- **Kısa süzgeçte doyum:** Tek bir inen nöronun 15 Hz'lik spike dizisi, 20 ms'lik süzgeçten sonra 90 Hz'e varan anlık sıçramalar üretiyor. Bu sıçramalar bacak ağını kalıcı doyuma (motor nöronlar ~200 Hz) kilitliyor.
- **300 ms'de ritim korunuyor:** İzlerde ritim, süzülmüş hız ~12 Hz'i geçtikten sonra (~550 ms) açıkça görülüyor. Skorun düşük olmasının nedeni baştaki sessiz dönem ve genlik dalgalanması.
- **Süzgeç seçimi (VARSAYIM):** 300 ms. Hız modeli girdisini bir popülasyon hızı olarak yorumluyor; 15 Hz'de bu süre ~4–5 spike aralığına denk geliyor.
- **Akson ucu geri bildirimi:** Hız ağı nöronlarının inen nöronlara sinapsları kordonda, inen nöronun akson uçlarında bulunuyor. Tek bölmeli LIF'te bu sinapslar beyindeki spike başlangıç bölgesini de susturuyor, bu yüzden kesildi (VARSAYIM). Ölçülen etkisi küçük.

### 8.5 Gövdede

Tüm koşular propriyosepsiyon kapalı, `--vnc rate`:
- **Sessiz beyin:** Tamamen hareketsiz (0 spike).
- **DNg100 17 Hz, 2,5 sn (ritim rejimi):** 2,8 sn'de 201 bacak motor nöronu spike'ı. Gövde 0,25 mm kıpırdıyor, 6° yalpalıyor. **Bacaklar adım atacak kadar hareket etmiyor.**
- **DNg100 150 Hz (LIF deneyi için seçilen hız):** Ağ doyuma gidiyor; bacak motor nöronları grup başına 100–400 spike/s. Sinek savruluyor (47°), sıçrama kası etkinleşiyor. Ritim yok.

**Propriyosepsiyon açık:**
- **Dinlenmede bile 2.000–3.500 hız nöronu etkin.** Yazarların ağında duyu nöronları girdi almıyordu, yani bu ölçek hiç kalibre edilmedi. Bizim tonik propriyoseptör hızlarımız hız ağında eşiğin yüzlerce katı girdi yaratıyor (tek bir kıl plakası grubunda 2.388 birim).
- **Sonuç:** Sessiz sinek kıpırdanıyor, duruşu bozuluyor.

### 8.6 Varsayımlar

| Parametre | Değer | Dayanak |
|---|---|---|
| Model parametreleri | Pugliese ve ark. | Makale ve yazarların MaleCNS yapılandırması |
| Eksik boyut | aynı tipin / süper sınıfın medyanı | %1,5 nöron |
| Boyut normalizasyonu | bacak motor ağının medyanı | Yazarlar ağın kendi medyanını kullanıyor |
| Spike → hız süzgeci | 300 ms | 8.4 |
| Akson ucu geri bildirimi | LIF'te kesik | 8.4 |
| Duyu nöronları | kodlayıcı hızına kelepçeli | Yazarların ağında 0 |
| Motor nöron spike'ları | hızdan Poisson | Kas modeli spike bekliyor |
| Kanat/karın/boyun ağları | LIF | 8.3 |

### 8.7 Sonuç

- **Başarılar:**
  - Yayımlanmış yürüme ritmi modeli MaleCNS'te yeniden üretildi.
  - Altı bacağın ağına genişletildi.
  - LIF beyinle birlikte çalışıyor.
- **Gövdeyi yürütmesi için üç engel (Z-33):**
  1. Ritim rejiminde motor çıktı çok düşük.
  2. Güçlü girdide ağ doyuma kilitleniyor.
  3. Duyu girdisinin ölçeği kalibre edilmemiş.
- **Sonraki yön:** Kullanıcıya soruldu.

## 9. Sineğin kendi gözleriyle görme (2026-09-17)

Karar: K-027. Kod: `flybrain/body/sight.py`, `EmbodiedFly(vision=...)`.

### 9.1 Yöntem

- **Kameralar:** NeuroMechFly'ın başına iki göz kamerası bağlı (FlyGym `add_vision`).
  - Görüş açısı 157°; yandan 27° öne bakıyor.
  - Çözünürlük 512 × 450.
  - Gözün kendi başını görmemesi için gizlenen parçalar FlyGym'deki gibi.
- **Kolon başına örnekleme:** Görüntü FlyGym'in 721 ommatidyumuna indirgenmiyor; konnektomdaki her kolon nöronu kendi bakış yönünden örnekleniyor.
  - **Bakış yönü:** Kolon koordinatları Faz 3'teki eşlemeyle φ, θ açılarına çevriliyor (senses/eye.py). Baş çerçevesinde x ileri, y sol, z yukarı; bu kural gövde modelinde doğrulandı.
  - **İzdüşüm:** Her karede baş ve kamera yönelimi fizikten okunuyor; yön, kameranın düz görüntüsüne izdüşürülüyor. Balık gözü düzeltmesine gerek kalmıyor.
  - **Kabul açısı:** 5°. Yedi noktalı, Gauss ağırlıklı bir örnekle uygulanıyor.
  - **Kapsam:** 7.378 görme nöronunun (L2, L3, Mi1, Tm3) tamamı kameraların görüş alanında.
- **Zamansal kodlama:**
  - **Yerel uyum:** Her kolon kendi parlaklığına uyum sağlıyor (1 sn). Kontrast, uyum sağlanan parlaklığa göre hesaplanıyor.
  - **Geçici hücreler (L2, Mi1, Tm3):** Kontrastın yüksek geçiren süzgeçten geçmiş halini görüyor (100 ms).
  - **Kalıcı hücreler (L3):** Kontrastın kendisini görüyor.
  - **Hıza çevirme:** Faz 3 ile aynı (K-012: açık/kapalı yöntemi, 250 Hz).
- **Yenileme:** 10 ms'de bir.

### 9.2 Neden zamansal kodlama? (K-027)

Faz 3'teki kodlama, tüm görüntünün ortalamasına göre sürekli kontrast üretiyordu. Durağan bir post görseli için bu yeterliydi. Gövdeli sinekte ise durağan sahne (beyaz gökyüzü, koyu zemin) sürekli bir uyarıma dönüştü:

| Koşul (sessiz beyin, yalnızca görme) | Görme uyarımı | LC4 | Dev lif (DNp01) | Bacak MN spike'ı |
|---|---|---|---|---|
| Durağan kodlama, 500 ms | ~900 kHz | 37 Hz | **63 Hz** | 308 |
| Uyumlu kodlama, 1 sn | 17–36 kHz | 0 | 0 | 27 |

Dev lif hiçbir şey hareket etmezken ateşliyordu, yani sinek sürekli kaçmaya çalışıyordu. Uyumlu kodlamada kalan uyarım, sineğin kendi küçük hareketlerinden geliyor (çökme, bacak seğirmeleri).

Biyolojik dayanak:
- L1 ve L2 hızlı ve geçici, L3 yavaş ve kalıcı yanıt veriyor. Mi1 ve Tm3'ün dürtü yanıtı çift fazlı (Yang ve Clandinin 2018; Arenz ve ark. 2017).
- Fotoreseptör ve lamina adaptasyonu saniyeler içinde gerçekleşiyor (Nikolaev ve ark. 2009).

### 9.3 Varsayımlar ve sınırlar

| Parametre | Değer | Dayanak |
|---|---|---|
| Uyum zaman sabiti | 1 sn | "Saniyeler içinde" (Nikolaev ve ark. 2009) |
| Geçici süzgeç | 100 ms | Kaynak yok; yayımlanmış sayılara ulaşılamadı |
| Yenileme | 10 ms | Çizim maliyeti; sineğin titreşim birleşme frekansı bunun üstünde |
| Kamera konumu | Başın ortası, iki göz aynı noktada | FlyGym modeli; iki göz arası paralaks yok |
| Kabul açısı | 5° | Faz 3 ile aynı |

Görüntü çizimi 10 ms'de bir yapılıyor ve beyin + gövde + görme döngüsü gerçek zamanın ~5 katı yavaş (1 sn için 4,9 sn).

## 10. Kaldığımız yer (2026-09-17)

> Bu bölüm sahneden önceki durumu anlatıyor; güncel durum [bölüm 13](#13-kaldığımız-yer-sahneden-sonra)'te.

**Bitenler:**

| Adım | Durum |
|---|---|
| Motor nöron → kas → eklem | ✅ Hortum, sıçrama, refleksler nöronlardan (6) |
| Propriyosepsiyon | ✅ İlk sürüm: FeCO ve kıl plakaları (7) |
| Sinir kordonu hız modeli | ⚠️ Deneysel (8); yürüme ertelendi (K-026) |
| Sineğin kendi gözleriyle görmesi | ✅ Zamansal uyumla (9) |

**Sıradakiler:**

1. **Instagram ekranlı sahne (K-021).** Hazırlık yapıldı, kod yazılmadı. Tasarım önerisi:
   - **Yüzey:** Sineğin önünde, sineği konum ve yönle izleyen kavisli bir yüzey. Önerilen boyutlar: 180°'lik yay, 6 mm uzaklık; zeminden başlıyor, gözden −10° ile +60° arasını kaplıyor.
   - **Görünürlük:** Yüzey fiziksel engel değil, yalnızca görülüyor.
   - **Uygulanabilirlik (doğrulandı):**
     - MjSpec'te kendi ağ geometrisi ve UV koordinatları olan bir yüzey tanımlanabiliyor (`add_mesh`: `uservert`, `userface`, `usertexcoord`).
     - Doku çalışma sırasında `model.tex_data` üzerinden değiştirilip her renderer'ın bağlamına `mjr_uploadTexture` ile yüklenebiliyor.
   - **Arena:** Arka plan gri; gökyüzü ve zemin kontrastı düşük tutulacak.
   - **Karar bekleyen konular:** Ekranın boyutu ve izleme biçimi (gövdeye kilitli mi, gecikmeli mi). Post görme alanının ne kadarını kaplayacak (K-014)?
2. **Yaklaşan nesne → kaçış testi (Z-25).** Gözler hazır; sahnede büyüyen bir disk dev lifi ateşletiyor mu?
3. **Hız (Z-21).** Döngü şu an gerçek zamanın ~5 katı yavaş; hedef 3 kat.
4. **Nöral karar ile gövdenin örtüşmesi (K-020, Z-27).** Faz 4 okumasında TTMn "yorum" kanalında; gövdeli sinekte kararlar zamansal görmeyle yeniden kalibre edilmeli.
5. **Faz 6: görselleştirme.** 3D sinek, 3D beyin, sineğin gördüğü, ekran ve karar günlüğü.
6. **Sonraya bırakılanlar:**
   - yürüme (Z-33),
   - yük ve zemin teması algısı (Z-32),
   - duruş tonusu (Z-29),
   - uçuş (Z-26).

## 11. Telefon ekranlı sahne (2026-09-17)

Kararlar: K-021, K-028. Kod: `flybrain/body/scene.py` (ekran ve arena), `flybrain/body/phone.py` (ekranın görüntüsü), `EmbodiedFly(scene=SceneConfig())`. Deney: `python -m flybrain.experiments.scene`.

### 11.1 Geometri

Kullanıcı ekranın önde geniş ama akıllı telefon oranında (9:19,5, dikey) olmasını istedi. Dar ve dikey bir telefonun geniş bir görme alanını kaplaması için ekran başın etrafında kıvrılıyor:

| Özellik | Değer |
|---|---|
| Biçim | Başın düşey ekseni etrafında silindir parçası, 180° |
| Uzaklık | 2 mm |
| Boyut | 6,3 mm (yay boyunca) × 13,6 mm |
| Doku | 540 × 1170 piksel |
| Malzeme | Işık yayıyor (aydınlatmadan etkilenmiyor); arkası koyu gri |
| Fizik | Çarpışma yok; sinek içinden geçebilir |

**Sinek telefonun hangi kısmını görüyor?**
- Gözler zeminden 0,7 mm yüksekte ve kolonların en üstü ~75° yukarı bakıyor. Bu yüzden sinek dikey telefonun yalnızca alt ~%60'ını görüyor.
- Post görseli bu bölgede: gezinme çubuğunun hemen üstünde (aşağı kaydırılmış akış).

**Yuva:** Gezinme çubuğu ekranın altında kalınca, kolonların en yoğun olduğu ufuk bandına (θ ≈ −19°…+7°) düşüyordu. Üç yerleşimi ölçtüm:

| Yerleşim | Ekranı gören kolon | Postu gören kolon | Sorun |
|---|---|---|---|
| 2 mm, zeminde | %69 | %37 | Post ufkun üstünde kalıyor |
| 1 mm, zeminde | %90 | %66 | Ön bacaklar (1,35 mm) ekranın içinden geçiyor |
| **2 mm, yuvada** | **%66** | **%62** | Gezinme çubuğu zeminin altında |

Seçilen yerleşimde telefon zemindeki bir yuvaya oturuyor ve post zemin hizasından başlıyor.

**İzleme:** Ekranın ekseni başın konumunu, yönü göğsün yönünü 500 ms zaman sabitiyle izliyor. Oturma bitince ekran gecikmesiz yerleştiriliyor.

**Arena ve ışık:**
- Gökyüzü gri (0,5); zemin 0,40/0,45 damalı, yansımasız.
- Işık yukarıdan gelen yönlü bir ışık (gölgesiz).
- MuJoCo'nun kameraya bağlı ışığı zayıflatıldı. Bu ışık göz kameralarıyla birlikte hareket ettiği için zeminin parlaklığı bakış açısına bağlı oluyordu.

### 11.2 Ekranın görüntüsü

Faz 8'e kadar yer tutucu bir Instagram akışı çiziliyor:
- **Sabit katman:** Durum çubuğu, başlık, gezinme çubuğu ve çerçeve.
- **Kayan akış:** Her post için kullanıcı satırı, 4:5 görsel, simgeler, beğeni, açıklama, yorum bağlantısı ve zaman.
- **Yazı tipi:** Yazılar Türkçe harfli bir yazı tipiyle (DejaVu Sans) çiziliyor; sinek onları yalnızca açık-koyu desen olarak görüyor.

Geçiş yolları:

| Yol | Açıklama |
|---|---|
| `scroll_to_post` (varsayılan, K-028) | Akış 400 ms'de, hızlı başlayıp yavaşlayarak bir post boyu kayar |
| `show_post` | Ekran bir karede değişir |
| `fade_to_post` | Eski ekran görüntüsü yenisine karışır |
| `play_video` | Bakılan postun görselinde video oynar (yaklaşma uyaranı bununla) |

**Güncelleme ve maliyet:**
- Ekran görüntüsü görmeyle aynı aralıkla (10 ms) yenileniyor.
- Doku modelde değiştirilip her çiziciye (göz kameraları, video kameraları) yeniden yükleniyor.
- Beyin, gövde, görme ve ekran birlikte gerçek zamanın ~4–5 katı yavaş.

### 11.3 Post geçişlerine yanıt (125 Hz, 12'şer post çifti)

Ekran baştan açık. Sinek 500 ms bakıyor, sonra sonraki posta geçiliyor ve 1,5 sn izleniyor. Beyne dışarıdan uyarım verilmiyor.

| Geçiş | Dev lif ateşleyen deneme | Ortalama spike | Göğüs hareketi | İlk 100 ms'deki görme uyarımı |
|---|---|---|---|---|
| Kaydırma, 400 ms | 12/12 | 8,8 | 2,1 mm | 198 kHz |
| Kaydırma, 1,2 sn | 12/12 | 18,1 | 2,4 mm | 175 kHz |
| Ani değişim | 5/12 | 1,9 | 0,4 mm | 118 kHz |
| Solarak geçiş, 300 ms | 2/12 | 0,6 | 0,2 mm | 27 kHz |

- **Ekranın açılması:** Ekran siyahken açılınca (görme uyarımı 173 kHz) dev lif ateşlemedi. 250 Hz'de bu durumda 28 spike'la kaçıyordu.
- **Kaydırmanın etkisi:** Ekran yakın olduğu için bir post boyu kaydırma sineğin gözünde ~80°'lik hızlı bir hareket; araya giren beyaz şerit ayrıca büyük bir parlaklık değişimi. LC4 30–100 spike üretiyor, dev lif ateşliyor.
- **Karar:** Kullanıcı kararıyla gerçek kaydırma kaldı ve sineğin kaçması modelin öngörüsü olarak kabul edildi (Z-35). *(Sonradan değişti: kaçış yaklaşmaya özgü çıkmadı, geçiş solma oldu; [bölüm 14](#14-telefon-korkusu-kontroller-dopamin-ve-ekran-2026-09-17), K-030.)*

**Videolar:**
- `runs/scene-kaydirma-0.mp4`: üstte dışarıdan görünüm, altta sineğin iki gözünün gördüğü.
- `runs/scene-acilis-0.mp4`: ekranın açılışı.

## 12. Yaklaşan nesne ve görme kazancı (2026-09-17)

Karar: K-029. Deney: `python -m flybrain.experiments.escape`.

### 12.1 Uyaran

**Yaklaşan disk:** Bakılan postun görselinde büyüyen koyu bir disk.
- Açısal yarıçap ψ(t) = atan(l/v / τ(t)); l/v = 40 ms (VARSAYIM).
- Tam açı 10°'den 160°'ye büyüyor, sonra 300 ms sabit kalıyor.
- Başlangıçtan çarpışma anına kadar 457 ms geçiyor.

**Geometri:** Diskin merkezi tam önde, ufkun 10° üstünde. Disk, kavisli ekranda her pikselin gözden bakış yönüne göre çiziliyor; bu yüzden ekranda yumurta biçimli, sineğin gözünde yuvarlak görünüyor.

### 12.2 Neden görme kazancı değişti?

250 Hz'de sinek durağan telefona bakarken çoğu denemede bir saniye içinde kaçıyordu. Tarama, nedenin sineğin kendi hareketi olduğunu gösterdi (Z-34):
- **Propriyosepsiyon kapalıyken** beyin tamamen sessiz kaldı.
- **Gövde sabitken** görme uyarımı 0,1 kHz'de kaldı ve kaçış olmadı.
- **Ekran siyahken bile** sinek kaçtı.

### 12.3 Kazanç taraması

Yaklaşma denemelerinde yalnızca bekleme sırasında kaçmamış ("temiz") denemeler sayılıyor. Durağan denemeler 0,76 sn ya da 3,3 sn sürüyor.

| Kazanç | Yaklaşan diske kaçış | İlk dev lif spike'ı (çarpışmaya göre, medyan) | Durağan ekranda kaçış |
|---|---|---|---|
| 250 Hz | 4/4 | −12 ms | 0,76 sn: 6/8 |
| 150 Hz | 18/18 | +7…+10 ms | 0,76 sn: 9/20; 3,3 sn: 6/12 |
| **125 Hz** | **20/22** | +25…+40 ms | 85 sn'de 5 ateşleme (3 sıçrama) |
| 100 Hz | 4/8 | +42 ms | 3,3 sn: 0/6 |
| 75 Hz | 0/7 | — | 0,76 sn: 2/8 (LC4 sessizken) |

**Propriyosepsiyon ısınması:**
- Propriyosepsiyon oturmanın sonunda açılıyordu. İlk 300 ms'de bacak motor nöronları sonrakinin ~2 katı ateşliyordu (14–21'e karşı 0–14 spike).
- Görme açılmadan önce 300 ms'lik ısınma eklendi.
- Kendiliğinden kaçışları ölçülebilir biçimde azaltmadı, ama bilinen bir yapaylığı kaldırıyor.

**Sonuç (125 Hz):**
- Yaklaşan disk denemelerin %91'inde dev lifi ateşletiyor ve sinek sıçrıyor.
- Durağan ekranda ~17 sn'de bir kendiliğinden ateşleme kalıyor.
- Gövdesiz sinek (Faz 3–4) 250 Hz'de kalıyor.

**Video:** `runs/escape-yaklasma-1.mp4` (4 kat ağır çekim). Sıçrayan sinek zaman zaman sırtüstü düşüyor; uçuş ve iniş denetimi yok (Z-26).

### 12.4 Açık konular

- **Zamanlama:** Dev lif, disk en büyük boyuna ulaştıktan sonra ateşliyor. Gerçek sineklerle nicel karşılaştırma yapılmadı (Z-25).
- **Kendiliğinden kaçışlar:** Kök neden dinlenen sineğin kıpırdanması. Duruş tonusu (Z-29) ve propriyosepsiyon kazancıyla (Z-33) birlikte ele alınmalı (Z-34).

## 13. Kaldığımız yer (sahneden sonra)

> Güncel durum [bölüm 15](#15-kaldığımız-yer-telefon-korkusundan-sonra)'te.

| Adım | Durum |
|---|---|
| Motor nöron → kas → eklem | ✅ (6) |
| Propriyosepsiyon | ✅ İlk sürüm (7) |
| Sinir kordonu hız modeli | ⚠️ Deneysel; yürüme ertelendi (8, K-026) |
| Sineğin kendi gözleriyle görmesi | ✅ (9) |
| Telefon ekranlı sahne | ✅ Dikey, kavisli, izleyen ekran; kaydırma (11, K-028) |
| Yaklaşan nesne → kaçış | ✅ %91, görme kazancı 125 Hz (12, K-029) |

**Sıradakiler:**
1. **Hız (Z-21):** Döngü gerçek zamanın ~4–5 katı yavaş; hedef 3 kat.
2. **Nöral karar ile gövdenin örtüşmesi (K-020, Z-27):**
   - Gövdeli sinekte zamansal görme ve 125 Hz'le kararlar yeniden kalibre edilmeli.
   - Kaydırmanın her seferinde kaçış tetiklemesi (Z-35) bu değerlendirmenin parçası.
3. **Faz 6: görselleştirme.** Videolardaki üst/alt düzen (dışarıdan görünüm, sineğin gözleri) ilk adım. Eksikler: 3D beyin, ekran ve karar günlüğü.
4. **Sonraya bırakılanlar:**
   - dinlenmede kıpırdanma ve duruş tonusu (Z-29, Z-34),
   - yürüme (Z-33),
   - yük algısı (Z-32),
   - uçuş (Z-26).


## 14. Telefon korkusu: kontroller, dopamin ve ekran (2026-09-17)

Kararlar: K-030 (K-028'in geçiş kısmının yerine geçti). Deneyler:
- `python -m flybrain.experiments.escape --rmax 125 --kontroller [--dopamin] [--tema acik]`
- `python -m flybrain.experiments.scene --no-extras --modes kaydir kaydir_hizli ani solma --themes acik koyu gri`

**Soru (kullanıcı):** Sinek kaçarsa akışı kaydıramaz. Telefondan korkmasının önüne nasıl geçilir? Telefona bakarken dopamin salgılatmak işe yarar mı?

### 14.1 Kaçış yaklaşmaya özgü mü?

Yaklaşan diske iki kontrol eklendi:
- **Kararma:** Diskin son hâlinin bölgesi büyümeden kararıyor. Zamanlama ve toplam kararma yaklaşmayla aynı; yalnızca kenarın dışa doğru hareketi yok.
- **Kayan görsel:** Yalnızca post görseli, kaydırmadaki gibi yavaşlayarak bir post boyu kayıyor. Ekranın geri kalanı duruyor; geniş alan hareketi var, geçen açık-koyu şerit yok.

Açık tema, 125 Hz, 8'er deneme:

| Uyaran | Dev lifin ateşlendiği deneme | Ort. dev lif spike'ı | Ort. LC4 spike'ı | Sıçrama |
|---|---|---|---|---|
| Yaklaşan disk | 8/8 | 17,5 | 178 | 8 |
| Kararma | 7/8 | 14,0 | 136 | 7 |
| Kaydırma | 8/8 | 9,4 | 96 | 7 |
| Kayan görsel | 1/8 | 0,5 | 7 | 1 |
| Durağan | 2/8 | 0,2 | 3 | 1 |

Aynı kontroller koyu temada (K-030), 8'er deneme:

| Uyaran | Dev lifin ateşlendiği deneme | Ort. dev lif spike'ı | Ort. LC4 spike'ı | Sıçrama |
|---|---|---|---|---|
| Yaklaşan disk | 5/8 | 8,0 | 68 | 5 |
| Kararma | 6/8 | 12,5 | 106 | 6 |
| Kaydırma | 8/8 | 11,2 | 123 | 7 |
| Kayan görsel | 4/8 | 1,5 | 10 | 3 |
| Solma (sonraki post) | 0/8 | 0 | 0 | 0 |
| Durağan | 0/8 | 0 | 1 | 0 |

**Koyu temada yaklaşmaya tepki zayıflıyor.** Başka bir seed ve 16 postla tekrarlandı; beklerken zaten kaçılan denemeler hariç:

| | Açık tema | Koyu tema |
|---|---|---|
| Yaklaşan disk | 14/15 (15,7 spike; LC4 179) | 12/14 (14,6 spike; LC4 130) |
| Solma | 1/15, sıçrama yok | 1/14, sıçrama yok |
| Beklerken kaçış | 1/16 | 2/16 |

- İki ölçümün toplamında yaklaşan diske kaçış açık temada 22/23 (%96), koyu temada 17/22 (%77).
- Nedeni ölçülmedi. Koyu temada ekranın geri kalanı da karanlık; kolonların uyum düzeyi ve diskin çevreyle kontrastı farklı.

- **Sonuç:** Kararma, yaklaşma kadar güçlü kaçış tetikliyor. İlk yoklamada (500 ms bekleme, farklı postlar) kararma yaklaşmadan da güçlüydü: 22,9 spike'a karşı 14,0.
- **Gerçek sinekle fark:** Yaklaşma algılayıcısı LPLC2 kararmaya ve geniş alan kaymasına yanıt vermiyor (Klapoetke ve ark. 2017). Modelde ise LC4 ve dev lif parlaklık değişimine de yanıt veriyor.
- **Kaydırmadaki kaçış:** Hareketten değil, ekrandan geçen geniş açık-koyu alanlardan geliyor. K-028'de kabul edilen "modelin öngörüsü" çerçevesi bu yüzden geri çekildi.
- **Olası neden (ölçülmedi):** Hareket yönü hesabı (T4/T5) hızlı ve yavaş girdilerin zaman farkına dayanıyor (Arenz ve ark. 2017). Modelde bütün nöronların zaman sabitleri aynı; görme yalnızca L2, L3, Mi1 ve Tm3'e veriliyor. Çözüm yolu Z-25'te.

### 14.2 Dopamin

Ödül nöronları (PAM, 316 nöron), beğeni kodlayıcısının en yüksek düzeyinde (~150 Hz) bütün deneme boyunca sürüldü. Açık tema, 8'er deneme:

| Uyaran | Dopaminsiz | Dopaminle |
|---|---|---|
| Kaydırma | 8/8, 9,4 spike, 7 sıçrama | 8/8, 7,0 spike, 5 sıçrama |
| Yaklaşan disk | 8/8, 17,5 spike, 8 sıçrama | 7/8, 13,1 spike, 6 sıçrama |
| Kararma | 7/8, 14,0 spike, 7 sıçrama | 8/8, 15,0 spike, 8 sıçrama |
| Kayan görsel | 1/8 | 2/8 |
| Durağan | 2/8 | 0/8 |

- **Sonuç:** Dopamin kaçışı önlemiyor; kaydırmada ve yaklaşmada sıçramaları biraz azaltıyor. İlk yoklamada kaydırmada fark yoktu (8/8'e karşı 8/8).
- **Neden:** Modelde dopamin hızlı, uyarıcı bir verici (K-008); yavaş reseptör etkileri ve öğrenme yok. Gerçek sinekte dopaminin irkilmeye bilinen etkisi de dev lif refleksini kesmek değil. DopR reseptörü üzerinden, elipsoid gövdede, tekrarlanan irkilmeden sonraki uyarılmışlığı düzenliyor (Lebestky ve ark. 2009).
- **İleride:** Öğrenme eklenince (Faz 10) ödülün telefonla eşleşmesi çekim yaratabilir; bu da refleksi doğrudan durdurmaz.

### 14.3 Ekran: tema ve geçiş

Kullanıcı yalnızca ekran tarafını seçti. Üç tema eklendi (`phone.THEMES`):
- **açık:** Instagram'ın varsayılanı;
- **koyu:** Instagram'ın karanlık modu;
- **gri:** zemin, post görsellerinin ortalama parlaklığında (0,5); gerçek Instagram'da yok.

Her tema dört geçişle ölçüldü (125 Hz, 12'şer geçiş; dev lifin ateşlendiği deneme, parantez içinde sıçrama):

| Tema | Kaydırma 400 ms | Kaydırma 250 ms | Anında | Solma 300 ms |
|---|---|---|---|---|
| Açık | 12/12 (11) | 8/12 (6) | 1/12 (1) | 1/12 (1) |
| Koyu | 11/12 (11) | 11/12 (7) | 2/12 (1) | 0/12 (0) |
| Gri | 9/12 (5) | 6/12 (4) | 6/12 (3) | 2/12 (3) |

- **Kaydırma:** Hiçbir temada güvenli değil. Gri tema spike sayısını düşürüyor (2,8'e karşı açıkta 9,3) ama önlemiyor. Koyu temada geçen siyah şerit kararma gibi etki ediyor.
- **Solma:** En düşük kaçış. Koyu temada tekrar ölçüldü: 2/12, bunlardan biri gerçek kaçış (12 spike, sıçrama). İlk ölçümle toplam: koyu 2/24, açık 3/24.
- **Gürültü:** 12 deneme az. Açık temada anında geçiş bir önceki ölçümde 5/12 çıkmıştı. Beklemede kaçışlar da var: gri temada 2 postta, açık ve koyu temada 1'er postta. Sıçrama sayısı beklemeyi de kapsıyor.
- **Karar (kullanıcı, K-030):**
  - Sonraki posta solarak geçiliyor: `EmbodiedFly.next_post`, 300 ms.
  - Ekran koyu temada. Kullanıcı, koyu temada yaklaşmaya tepkinin zayıfladığı (14.1) öğrenildikten sonra da koyu temayı seçti.
  - Kaydırma, anında geçiş ve öteki temalar deneyler için duruyor.
- **Bedel:**
  - Instagram akışında solma yok.
  - Koyu temada yaklaşan diske kaçış %96'dan %77'ye iniyor.
  - Faz 8'de gerçek ekran görüntüleri karanlık modda alınmalı.

**Video:** `runs/scene-solma-koyu-0.mp4`. Koyu tema; sinek bakıyor, akış iki kez solarak sonraki posta geçiyor.

## 15. Kaldığımız yer (telefon korkusundan sonra)

| Adım | Durum |
|---|---|
| Motor nöron → kas → eklem | ✅ (6) |
| Propriyosepsiyon | ✅ İlk sürüm (7) |
| Sinir kordonu hız modeli | ⚠️ Deneysel; yürüme ertelendi (8, K-026) |
| Sineğin kendi gözleriyle görmesi | ✅ (9) |
| Telefon ekranlı sahne | ✅ Dikey, kavisli, izleyen ekran; koyu tema, solarak geçiş (11, 14, K-028, K-030) |
| Yaklaşan nesne → kaçış | ✅ Çalışıyor: açık temada %96, koyu temada %77. Yaklaşmaya özgü değil, kararma da aynı güçte (12, 14, Z-25) |

**Sıradakiler:**
1. **Hız (Z-21):** Döngü gerçek zamanın ~4–5 katı yavaş; hedef 3 kat.
2. **Nöral karar ile gövdenin örtüşmesi (K-020, Z-27):** Gövdeli sinekte zamansal görme, 125 Hz ve solarak geçişle kararlar yeniden kalibre edilmeli.
3. **Faz 6: görselleştirme.** Videolardaki üst/alt düzen (dışarıdan görünüm, sineğin gözleri) ilk adım. Eksikler: 3D beyin, ekran ve karar günlüğü.
4. **Faz 7'den önce:** Kaçışın yaklaşmaya özgüllüğü (Z-25). Korkutucu içeriğe tepkinin anlam taşıması için gerekli.
5. **Sonraya bırakılanlar:**
   - dinlenmede kıpırdanma ve duruş tonusu (Z-29, Z-34),
   - yürüme (Z-33),
   - yük algısı (Z-32),
   - uçuş (Z-26).
