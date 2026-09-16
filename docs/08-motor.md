# 08 — Motor Kod Çözücü (Faz 4)

> 2026-09-16. Kod: [`flybrain/motor/`](../flybrain/motor/), [`flybrain/fly.py`](../flybrain/fly.py). Deneyler: [`flybrain/experiments/motor.py`](../flybrain/experiments/motor.py), [`flybrain/experiments/calibrate.py`](../flybrain/experiments/calibrate.py)

Soru: Sinir aktivitesinden hangi Instagram eylemini, nasıl okuyacağız?

## 1. Komut nöronları yetmiyor

Mimaride ilk plan, her eylemi literatürdeki bir "komut nöronuna" bağlamaktı (DNp09/oDN1 ileri yürüme, MDN geri yürüme, MN9 hortum, P1 kur yapma...). 32 gerçekçi post (doğal istatistikli görsel + rastgele caption) × 2 deneme, 1 saniye:

| havuz | nöron | ateşleyen deneme | ort. Hz | en çok Hz | tutarlılık (r) |
|---|---|---|---|---|---|
| ileri_yuru (DNp09, oDN1) | 4 | %0 | 0 | 0 | – |
| geri_yuru (MDN) | 4 | %5 | 0,0 | 0,2 | −0,05 |
| hortum (MN9) | 2 | %100 | 1,1 | 1,5 | 0,52 |
| yutma (MN11/12) | 9 | %0 | 0 | 0 | – |
| sarki (pIP10, vPR6) | 10 | %89 | 0,2 | 0,2 | 0,56 |
| kur (P1) | 49 | %0 | 0 | 0 | – |
| kacis (Giant Fiber) | 2 | %86 | 4,1 | 14,0 | 0,95 |
| don_sol / don_sag (DNa02) | 1 / 1 | %16 | 0,2 | 2,0 | ~0 |
| timar (aDN1/2) | 4 | %0 | 0 | 0 | – |

"Tutarlılık", aynı postun iki denemesi arasındaki korelasyondur.

- **Sinek bu haliyle feed'i hiç kaydıramaz:** ileri yürüme komut nöronları hiç ateşlemedi.
- **Giant Fiber ateşliyor ve posta özgü yanıt veriyor.** Gerçek sinekte de görsel tehdit sinyali alan bu nöron, postların %86'sında ateşledi.
- **Her post ortalama 128 inen nöronu aktive ediyor** (en az 75, en çok 196). Yani bilgi vücuda iniyor, ama tek tük komut nöronları bu bilginin çok küçük bir kısmını yakalıyor.

Özel sondalar (nöron başına Hz):

| sonda | hortum (MN9) | kacis | geri_yuru | aktif inen nöron |
|---|---|---|---|---|
| gri ekran | 0 | 0 | 0 | 0 |
| şeker | 2,0 | 0 | 0 | 68 |
| acı | 0 | 0 | 0 | 62 |
| ödül (20 bildirim) | 0 | 0 | 0 | 8 |
| yalnız koku | 1,2 | 0 | 0,6 | 156 |

## 2. Kas grupları: vücut bölgesine göre okuma (K-015)

MaleCNS, motor nöronları ve inen nöronları **hedefledikleri vücut bölgesine** göre etiketliyor (`subclass`). Aynı 32 post için kas grupları:

| grup | nöron | aktif deneme | Hz/nöron | tutarlılık (r) | postlar arası / deneme içi std |
|---|---|---|---|---|---|
| ön bacak MN (fl) | 135 | %100 | 0,05 | 0,73 | 2,47 |
| orta bacak MN (ml) | 116 | %100 | 0,07 | 0,64 | 2,12 |
| arka bacak MN (hl) | 130 | %100 | 0,06 | 0,38 | 1,45 |
| boyun MN (nm) | 24 | %100 | 0,69 | 0,57 | 1,89 |
| haltere MN (hm) | 16 | %100 | 0,27 | 0,67 | 2,16 |
| karın MN (ad) | 214 | %97 | 0,03 | 0,80 | 2,94 |
| kanat güç kasları (DLM/DVM) | 24 | %97 | 0,40 | 0,94 | 5,53 |
| kanat yönlendirme kasları | 43 | %100 | 1,26 | 0,74 | 2,57 |
| hortum MN (beyin, pm) | 67 | %100 | 0,07 | 0,93 | 4,81 |
| boyun MN (beyin, nm) | 20 | %100 | 0,46 | 0,41 | 1,54 |
| inen nöron: bacaklar (xl) | 275 | %100 | 0,22 | 0,79 | 2,78 |
| inen nöron: üst tectulum (ut) | 276 | %100 | 0,20 | 0,94 | 5,36 |
| inen nöron: alt tectulum (lt, kaçış) | 31 | %100 | 1,48 | 0,98 | 8,70 |

"Postlar arası / deneme içi std", yanıtın içeriğe ne kadar duyarlı olduğunu gösterir: 1'den büyük değerler, posttan posta değişimin aynı postun tekrarındaki değişimden büyük olduğu anlamına gelir.

- **Neredeyse her kas grubu her postta aktif ve yanıtlar içeriğe duyarlı** (oran 1,45–8,70).
- **Biyolojik açıdan anlamlı sondalar:**
  - **Acı:** bacaklara giden inen nöronları güçlü sürüyor (454 spike) ve karın kaslarını çalıştırıyor. Sinek uzaklaşıyor.
  - **Şeker:** bacaklarla birlikte hortum kaslarını sürüyor.
- **Karar:** okuma bu kas gruplarından yapılır. Kanallar ve nöronlar [`flybrain/motor/readout.py`](../flybrain/motor/readout.py) dosyasında tanımlı.

| kanal | eylem | nöronlar |
|---|---|---|
| ileri | sonraki posta geç | bacak MN'leri (fl + ml + hl), 381 |
| geri | önceki posta dön | MDN, 4 |
| hortum | beğen / kaydet | beyin hortum MN'leri (pm), 67 |
| yorum | yorum yap | kanat yönlendirme MN'leri, 43 |
| takip | takip et | karın MN'leri, 214 |
| cikis | takipten çık / oturumu bitir | alt tectulum inen nöronları, 31 |
| sekme | sekme değiştir (sol/sağ) | boyun MN'lerinde sol − sağ farkı, 44 |
| timar | boşta bekle | ön bacak hızı − orta/arka bacak hızı |

## 3. Normalizasyon: eylemlerin genel sıklığını kim belirler? (K-016)

İlk 500 ms'lik pencerede, 64 denemede, farklı kurallar:

| kural | sonuç | iki denemede aynı karar |
|---|---|---|
| **Ham** (en hızlı ateşleyen kanal kazanır) | Yalnızca "yorum" (34) ve "çıkış" (30). Kanat ve kaçış nöronları doğal olarak hızlı ateşliyor. | %94 |
| **Nötr z-skor** (her kanal referans postlara göre ölçeklenir, en büyük z kazanır) | Tüm eylemlere yakın eşit dağılım. Yorum ve takip de postların yaklaşık 1/9'unda. | %34 |
| **Eylem bütçesi** (z-skor + genel sıklıklar insan tarafından) | Çoğunlukla kaydırma; arada beğeni, tımar, nadiren çıkış | %66 |

**Kullanıcı kararı: eylem bütçesi.** Genel sıklıkları insan belirliyor; hangi postun beğenileceğini, hangisinde yorum yapılacağını sinek seçiyor.

## 4. Kullanıcı kararları: takip ve kaydet

- **Takip et → karın kasları (K-017).** P1 nöronları hiçbir postta ateşlemedi. Erkek sineğin kur yapmasının son aşaması karnını bükmek (çiftleşme girişimi). Karın MN'leri postların %97'sinde aktif ve yanıtları posta özgü (r = 0,80).
- **Kaydet → çok güçlü hortum yanıtı (K-018).** Yutma nöronları (MN11/12) hiç ateşlemedi. Beğen ve kaydet aynı kanaldan okunuyor ve iki şiddet eşiği bilinçli olarak ayrılıyor:
  - **Beğeni eşiği:** referans postların %15'inde hortum kararı çıkacak biçimde ayarlanır.
  - **Kaydetme eşiği:** hortum kararlarının en fazla ~%13'ünü (2/15) kaydetmeye gönderen en küçük z değeri; ayrıca beğeni eşiğinin en az 1 standart sapma üstünde olmak zorunda.
  - Seçilen değerler ve doğrulama: [6.3](#63-beğeni-ve-kaydetme-şiddetleri-k-018).

## 5. Karar döngüsü

1. **Kaydırma:** 300 ms gri ekran; önceki postun izi söner. Beyin sıfırlanmaz.
2. **Bakış:** post 500 ms'lik pencerelerle, en fazla 3 pencere (1,5 sn) izlenir. Her pencerenin sonunda kanal hızları, bakış başından beri **biriken** spike'lardan hesaplanır ve z-skora çevrilir. Ortalama ve standart sapma, aynı birikim süresi için referans postlardan ölçülür; standart sapmaya sayma gürültüsü tabanı uygulanır.
3. **Seçim:** eşiğini aşan kanallar arasından eşiği en büyük farkla aşan seçilir. Hiçbiri aşmazsa bir pencere daha izlenir.
4. **İlgi kaybı:** 3 pencere sonunda hâlâ karar yoksa sinek "ilgisini kaybeder" ve sonraki posta geçer.
5. **Homeostaz:** her karardan sonra eşikler bütçeye doğru küçük bir adım kaydırılır (6.5).

Eylem bütçesi (K-016):

| kanal | ileri | geri | hortum (beğen + kaydet) | yorum | takip | çıkış | sekme | tımar |
|---|---|---|---|---|---|---|---|---|
| bütçe | %35 | %3 | %15 (kaydet %2) | %2 | %2 | %2 | %5 | %5 |

Eşikler, kanallar arası yarış hesaba katılarak gerçekleşen oranlar bütçeye eşit olacak şekilde belirlenir (6.2).

## 6. Kalibrasyon ve doğrulama

### 6.1 İlk denemeler ve bulunan sorunlar

Kalibrasyon için 480 referans post kullanıldı. Doğrulama için kalibrasyonda kullanılmamış 160 post, 2 tekrar kullanıldı.

1. **Birinci deneme:** her pencere ayrı değerlendirildi, eşikler her kanalın en yüksek z-skor kantilinden seçildi, standart sapmada taban yoktu.
   - Kalibrasyon istatistikleri, motor yanıtının neredeyse tamamen ilk 500 ms'de toplandığını gösterdi (Z-20). Sonraki pencerelerde standart sapma 0,001 düzeyindeydi, yani tek bir spike z ≈ 30 üretebilirdi.
   - Doğrulama tamamlanmadan durduruldu.
2. **İkinci deneme:** sayma gürültüsü tabanı eklendi, pencereler yine ayrı değerlendirildi. Doğrulama sonuçları bütçeden uzaktı:
   - beğeni + kaydet %3,7 (hedef %15)
   - hortum eylemlerinin %33'ü kaydetme (hedef ~%13). Seyrek pencerelerde 2 spike beğeni, 3 spike kaydetme demekti.
   - karar tutarlılığı %57
   - Nedenler: kanallar arası yarış hesaba katılmamıştı; geç pencereler seyrekti.

### 6.2 Düzeltilmiş kalibrasyon

- **Sayma gürültüsü tabanı:** standart sapma, tek bir spike'ın o birikim süresinde yarattığı hızdan küçük olamaz.
- **Birikimli kanıt:** w. pencerede z-skor, bakış başından beri biriken spike'lardan hesaplanır. Ortalama ve standart sapma, aynı birikim süresi için referanstan ölçülür.
- **Bütçeye gerçekleşen oranla uyum:** Karar kuralı 480 referans postta bütünüyle uygulanır. Her kanalın eşiği, o eylemin gerçekleşen oranı bütçeye eşitlenene kadar ikiye bölme yöntemiyle ayarlanır; birkaç tur tekrarlanır çünkü kanallar birbirini etkiliyor.
- **Muhafazakâr kaydetme eşiği:** hortum kararlarının en fazla %13'ünün kaydetme olacağı en küçük z değeri seçilir; ayrıca beğeni eşiğinin en az 1 standart sapma üstünde olmalı.

Ham referans hızları `runs/calibration-rates-*.npz` dosyasına kaydediliyor. Eşikler yeniden simülasyon yapmadan `--fit-from` ile yeniden hesaplanabiliyor.

Eşikler ([`flybrain/motor/calibration.json`](../flybrain/motor/calibration.json)):

| kanal | bütçe | eşik (z) | birikimli ort. Hz (0,5 / 1 / 1,5 sn) | referansta gerçekleşen |
|---|---|---|---|---|
| ileri | %35 | −0,25 | 0,072 / 0,036 / 0,025 | %35,6 |
| geri | %3 | 1,71 | 0,558 / 0,279 / 0,186 | %1,9 |
| hortum | %15 | 0,67 | 0,079 / 0,039 / 0,026 | %15,2 |
| yorum | %2 | 1,20 | 1,470 / 0,736 / 0,492 | %1,9 |
| takip | %2 | 1,29 | 0,030 / 0,015 / 0,010 | %1,9 |
| cikis | %2 | 2,05 | 2,322 / 1,466 / 1,158 | %2,1 |
| sekme | %5 | 1,55 | 0,190 / 0,095 / 0,064 | %5,2 |
| timar | %5 | 1,06 | −0,047 / −0,024 / −0,017 | %4,8 |
| **kaydet** | %2 | **2,63** | | %0,8 |
| ilgi kaybı | – | | | %31,5 |

"Geri" %1,9'da kaldı. Spike sayıları tam sayı olduğu için gerçekleşen oran kademeli değişiyor ve %3'e tam oturmuyor.

### 6.3 Beğeni ve kaydetme şiddetleri (K-018)

Hortum kanalındaki z-skor kademeli: her kademe, ilk yarım saniyede 67 hortum motor nöronunda **bir spike daha** demek. Referans postlarda tipik yanıt yaklaşık 2,6 spike, standart sapma yaklaşık 2 spike.

| hortum yanıtı (ilk 0,5 sn) | z | sonuç | hortum kararları içindeki payı |
|---|---|---|---|
| en az 4 spike | ≥ 0,67 | **beğen** | %100 (hortum kararlarının tamamı) |
| en az 7 spike | ≥ 2,14 | (seçilmedi) | %20,5 |
| **en az 8 spike** | **≥ 2,63** | **kaydet** | **%5,5** |

Kaydetme payı hedefi (~%13) tam tutturulamıyor. "Kaydetme beğeniyi yutmasın" isteği doğrultusunda, payı bu hedefi aşmayan en küçük kademe seçildi.

### 6.4 Sabit eşiklerle doğrulama (160 ayrı post × 2 tekrar)

| eylem | bütçe | gerçekleşen |
|---|---|---|
| ileri | %35 | %26,6 |
| beğen | | %7,2 |
| kaydet | %2 | %0,6 |
| (beğen + kaydet) | %15 | %7,8 |
| yorum | %2 | %3,8 |
| sekme (sol + sağ) | %5 | %5,6 |
| tımar | %5 | %4,1 |
| geri | %3 | %2,5 |
| çıkış | %2 | %1,2 |
| takip | %2 | %0,9 |
| ilgi kaybı | – | %47,5 |

- **Kaydetme payı:** hortum eylemlerinin %8'i. Sınırın (≤ %13) içinde. ✅
- **Karar tutarlılığı:** iki tekrarda aynı karar %49.
- **Bakma süresi:** kararların %51'i 0,5 sn'de, %48'i 1,5 sn'de (ilgi kaybı).
- **Sorun:** ileri ve beğeni, referanstaki oranların altında kaldı.

Olası nedenler:
1. Kalibrasyonda sinek her posta 1,5 sn bakıyordu; gerçek kullanımda çoğu zaman 0,5 sn'de karar verip kaydırıyor. Bu yüzden sonraki post, sinapsları farklı bir yorgunluk düzeyindeyken başlıyor.
2. Referans ve test postları farklı örneklerden geliyor.

### 6.5 Eşik homeostazı (K-016 eki)

Gerçek Instagram içeriği referans postlardan zaten farklı olacak; sabit eşikler her durumda kayacak. Bu yüzden kullanımda eşikler her karardan sonra küçük adımlarla (0,05 z) bütçeye doğru ayarlanıyor:

- Bir eylem bütçesinden sık seçiliyorsa eşiği yükseliyor, seyrek seçiliyorsa düşüyor.
- Kaydetme eşiğinin kendi denetleyicisi var. Bu denetleyici yalnızca hortum kararlarında çalışıyor, bu kararlar içindeki kaydetme payını ~%13'e (2/15) çekiyor ve adımı 0,15 z. Kaydetme eşiği her zaman beğeni eşiğinin en az 1 standart sapma üstünde kalıyor.
- Homeostaz yalnızca **genel sıklığı** ayarlıyor. Hangi postun daha güçlü yanıt aldığı tamamen sineğin sinir aktivitesine bağlı.

**Test:** 3 sinek, her biri kendine ait farklı postları art arda izliyor, homeostaz açık. Yeniden üretmek için:

```bash
python -m flybrain.experiments.calibrate --skip-calibration --homeostasis-test --flies 3 --session 300
```

**Birinci sürüm** (kaydetme denetleyicisi tüm postlarda, adım 0,05 × %2), 3 × 240 post:

| eylem | bütçe | post 1–80 | 81–160 | 161–240 |
|---|---|---|---|---|
| ileri | %35 | %28,7 | %34,2 | %31,2 |
| beğen + kaydet | %15 | %7,9 | %9,2 | %12,1 |
| kaydet | %2 | %0 | %0 | %0 |
| ilgi kaybı | – | %42,9 | %41,7 | %37,1 |

- Beğeni bütçeye doğru çıkıyor.
- **Kaydetme hiç gerçekleşmedi.** Nadir bir hedefte adım çok küçük kaldı (kaydetmesiz her postta −0,001 z). Eşik 240 postta yalnızca 2,63'ten 2,39'a indi; bir kademe aşağı inmek için 0,49 düşmesi gerekiyordu.

**İkinci sürüm** (kaydetme denetleyicisi yalnızca hortum kararlarında, pay hedefi ~%13, adım 0,15), 3 × 300 post:

| eylem | bütçe | post 1–100 | 101–200 | 201–300 |
|---|---|---|---|---|
| ileri | %35 | %29,7 | %35,0 | %32,3 |
| beğen + kaydet | %15 | %8,7 | %9,0 | **%14,0** |
| kaydet | %2 | %0 | %0 | %0,7 |
| geri | %3 | %1,7 | %3,3 | %2,3 |
| yorum | %2 | %2,0 | %1,3 | %1,7 |
| takip | %2 | %2,0 | %0 | %1,7 |
| çıkış | %2 | %3,7 | %2,3 | %3,7 |
| sekme | %5 | %4,0 | %4,3 | %4,3 |
| tımar | %5 | %5,0 | %6,0 | %4,3 |
| ilgi kaybı | – | %43,3 | %38,7 | %35,7 |

- **Beğeni:** son blokta bütçeye ulaştı (%14).
- **Kaydetme:** eşik 2,63'ten 2,03–2,14'e indi (7 spike kademesi); kaydetmeler son blokta başladı. Oturum boyunca hortum eylemlerinin %2'si kaydetme; hedef %13'e doğru yaklaşıyor ama 300 post yetmedi.
- **Diğer eylemler:** bütçelerine yakın. Bu nadir eylemlerde blok başına yalnızca 300 bakış olduğu için ±1 puanlık oynamalar örnekleme gürültüsü.
- **Başlangıç tercihi:** Kaydetme bilinçli olarak muhafazakâr bir noktadan başlıyor; azdan çoğa doğru ayarlanıyor. Eşik durumu (`ActionSelector.state()`) Faz 8'de oturumlar arasında saklanacak, böylece bu geçiş yalnızca ilk kullanımda yaşanacak.

### 6.6 Nötr uyaran

Gri ekran ve boş caption verildiğinde sinek hiçbir eylem seçmiyor; 1,5 sn sonra ilgisini kaybedip kaydırıyor (`tests/test_brain_params.py`).
