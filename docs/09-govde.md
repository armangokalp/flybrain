# 09 — Gövde (bedenlenme)

> Durum: **Faz 5 başladı (2026-09-17).** Bu belge, sineğin 3D fizik gövdesini kendi motor nöronlarıyla hareket ettirme çalışmasını anlatır. Kararlar: K-019, K-020, K-021, K-022.

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
- **Pasif duruş:** Motor girdisi sıfırken sinek eklem yaylarıyla ayakta duruyor.
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

- [ ] Beyin sessizken gövde pasif duruşta kalıyor
- [ ] MN9 uyarımı → hortum uzuyor; şeker tadı → MN9 → hortum uzuyor (uçtan uca)
- [ ] Dev lif (DNp01) uyarımı → TTMn → orta bacaklar açılıyor → sinek sıçrıyor
- [ ] DNg100 uyarımı → bacaklarda ritmik hareket (ne kadar yürüdüğü ölçülüp raporlanır)
- [ ] Bacak hareketi → propriyoseptif duyu nöronları ateşliyor
- [ ] Nöral kararlar ile gövde hareketinin örtüşmesi ölçülüyor
- [ ] Kapalı döngü (beyin + gövde + görme) gerçek zamanın en fazla 3 katı yavaşlıkta
