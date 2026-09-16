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
- [ ] Bacak hareketi → propriyoseptif duyu nöronları ateşliyor
- [ ] Nöral kararlar ile gövde hareketinin örtüşmesi ölçülüyor
- [ ] Kapalı döngü (beyin + gövde + görme) gerçek zamanın en fazla 3 katı yavaşlıkta

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

1. **Gövdeden beyne his (Z-23):**
   - kordotonal organ, kampaniform sensiller, tarsal temas
   - Hem yürüme koordinasyonu hem duruş tonusu için gerekli (Z-29).
2. **Sineğin gözleriyle görme:** Ommatidyumları konnektom göz kolonlarına bağlamak.
3. **Sahne:** Sineği izleyen Instagram ekranı.
4. **Kapalı döngü hızı:**
   - Sessiz beyinle 1 sn simülasyon: videosuz yaklaşık 3 sn, iki kameralı kayıtla 6 sn.
   - Hedef: gerçek zamanın en fazla 3 katı.
5. **Nöral karar ile gövde tutarlılığı (Z-27):**
   - Faz 4 okumasında TTMn ve STTMm (sıçrama kasları) "yorum" kanalında sayılıyor; "çıkış" kanalına taşınmalı.
   - Bu değişiklik yeniden kalibrasyon gerektiriyor.
