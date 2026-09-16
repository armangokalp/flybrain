# 04 — Yol Haritası

Her faz, bitiş kriterleri sağlanmadan kapanmaz. Gerçek Instagram hesabına ilk dokunuş **Faz 8**'de olacak; o zamana kadar her şey yerelde test edilir. 2026-09-17'de sineğin 3D gövdesi ve görselleştirme eklendi, Instagram bağlantısı iki faz ertelendi (K-022).

## Faz 0 — Araştırma ve mimari ✅

- [x] Veri setinin güncel durumunu araştırmak (MaleCNS v1.0, Eylül 2026)
- [x] Referans simülasyon modellerini belirlemek (Shiu ve ark. LIF)
- [x] Mimari taslağı, ilkeler ve zorluklar belgeleri
- [x] Açık tasarım kararlarının netleştirilmesi (K-004, K-005, K-006)

**Bitiş:** Mimari onaylandı, veri indirme izni alındı.

## Faz 1 — Konnektom veri hattı ✅

- [x] Python ortamı (`pyproject.toml`, sanal ortam)
- [x] İndirme betiği: anotasyonlar, nörotransmitterler, bağlantı ağırlıkları
- [x] Nöron filtresi (yalnızca izlenmiş/anotasyonlu gövdeler)
- [x] Seyrek ağırlık matrisi + işaretler → önbellek (`data/cache/`)
- [x] Veri keşif raporu ve aday nöronların doğrulanması ([05-veri-kesfi.md](05-veri-kesfi.md))

**Bitiş:** `load_connectome()` birkaç saniyede matrisi yüklüyor; aday nöron listesi doğrulanmış. ✅ (2026-09-16: önbellek 3 sn'de üretiliyor, 9 motor + 8 duyu havuzunun hepsi dolu, 7 test geçiyor)

## Faz 2 — Simülasyon çekirdeği ✅

- [x] LIF motoru (olay güdümlü, seyrek); isteğe bağlı sinaptik depresyon ve adaptasyon
- [x] Performans ölçümü: simülasyonun 1 saniyesi yaklaşık 1,2 saniye
- [x] **Doğrulama:** şeker tat nöronlarının (LB3b/c) uyarılması MN9'u ateşliyor mu, acı nöronlarının (LB1a–d) uyarılması ateşletmiyor mu? Orijinal ağırlıklarla evet (166 / 14 Hz), fakat beyin kilitleniyor (Z-06)
- [x] Ağırlık ölçeği ve mekanizma taraması (35 ayar), koku ayırt edilebilirliği ölçütü ([06-simulasyon.md](06-simulasyon.md))
- [x] Kararlılık testleri: kalıcı çekici bulundu ve kararlı ayarlar belirlendi
- [x] Çalışma ayarının seçimi: B (K-011), `BRAIN_PARAMS`

**Bitiş:** Doğrulama deneyi yayınlanmış sonuçla nitel olarak uyuşuyor; 500 ms'lik bir karar penceresi makul sürede hesaplanıyor. ✅ (2026-09-16: seçilen ayarda şeker → MN9 3,7 Hz, acı → 0 Hz; kalıcı aktivite yok; 500 ms ≈ 0,6 sn)

## Faz 3 — Duyu kodlayıcıları ✅

- [x] Görme: görsel → panoramik kolon eşlemesi → ON/OFF giriş nöronları, 250 Hz (K-012, K-014)
- [x] Göz geometrisi ve koordinatsız nöronların kolonlarının bağlantıdan çıkarılması (Z-09)
- [x] Katman katman sinyal yayılımı ve üç giriş yönteminin karşılaştırması (Z-02)
- [x] Koku: kelime → 3 glomerül, doygun karışım (K-013)
- [x] Ödül/ceza: bildirim → PAM/PPL1 uyarımı
- [x] Birleşik test: görsel + caption (16 post, %85)

**Bitiş:** Farklı görseller inen nöronlarda ayırt edilebilir aktivite desenleri üretiyor. ✅ (2026-09-16: 16 doğal istatistikli görsel %95–100, 16 post %85; gri ekranda sessiz, post sonrası dinlenime dönüyor)

## Faz 4 — Motor kod çözücü ✅

- [x] Motor okuma: komut nöronları ölçüldü; kas grubu kanallarına geçildi (K-015)
- [x] Kalibrasyon: 480 içerikten bağımsız referans post, birikimli kanıt, sayma gürültüsü tabanı, bütçeye gerçekleşen oranla uyum (K-016)
- [x] Eylem seçimi, "bakmaya devam" ve ilgi kaybı; eşik homeostazı
- [x] "Beğen" ve "kaydet" (iki şiddet, K-018), "takip et" (karın kasları, K-017)
- [x] `Fly` sınıfı: bir posta bakma döngüsü

**Bitiş:** Gri ekranda hiçbir eylem tetiklenmiyor; gerçek görsellerde eylem dağılımı dejenere değil (tek bir eylem baskın değil). ✅ (2026-09-16: gri ekran → ilgi kaybı; homeostazlı oturumlarda eylemler bütçeye yakın dağılıyor, beğeni son blokta %14)

## Faz 5 — Gövde (bedenlenme)

Ayrıntı: [09-govde.md](09-govde.md). Kararlar: K-019, K-020, K-021.

- [x] Gövde kütüphanesi (FlyGym 2.1, NeuroMechFly): 126 eklem serbestlik derecesi, fizik gerçek zamandan hızlı
- [x] Yürüme ritmi yoklaması: DNg100 → ritim çekirdeği → bacak motor nöronları (Z-22)
- [x] Ölçülmüş elektriksel sinapslar: dev lif → TTMn, PSI (K-023)
- [x] Motor nöron → kas → eklem tablosu (bacaklar, baş, hortum, kanatlar, karın, sıçrama) ve kas modeli (Z-24, ilk sürüm)
- [ ] Gövdeden beyne his: eklem açısı, yük, zemin teması, baş konumu (Z-23)
- [ ] Sineğin gözleriyle görme: ommatidyumlar → konnektom göz kolonları
- [ ] Sahne: serbest sinek ve onu izleyen Instagram ekranı (K-021)
- [ ] Kapalı döngü (beyin + gövde + görme) ve hız iyileştirmesi (Z-21)
- [x] Neden–sonuç testleri: MN9 → hortum ✅, dev lif → sıçrama ✅ (K-023), DNg100 → bacaklar kıpırdıyor ama yürüme yok, şeker → kısmi (Z-30)
- [ ] Nöral karar ile gövde hareketinin örtüşme ölçümü (K-020, Z-27)

**Bitiş:**
- Beyin sessizken gövde hareketsiz.
- Uyarılan her motor devresi, beklenen gövde bölgesini hareket ettiriyor.
- Kapalı döngü gerçek zamanın en fazla 3 katı yavaşlıkta çalışıyor.

## Faz 6 — Görselleştirme ve kayıt

- [ ] Oturum kaydı: spike'lar, gövde pozları, sineğin göz görüntüsü, ekran, kararlar
- [ ] Yerel izleme paneli, senkron görünümler:
  - 3D sinek
  - 3D beyin (her spike nöronun gerçek konumunda)
  - sineğin gördüğü
  - Instagram ekranı
  - karar günlüğü
- [ ] Canlı mod (ağır çekim, açıkça etiketli) ve gerçek hızda oynatma (Z-28)
- [ ] Beyin bölgesi yüzeyleri ve önemli nöronların şekilleri (indirme için ayrıca izin istenecek)
- [ ] Paylaşılabilir video dışa aktarımı

**Bitiş:** Bir oturum baştan sona izlenebiliyor. Görülen her hareket, o anda ateşleyen motor nöronlara kadar geriye doğru izlenebiliyor.

## Faz 7 — Yerel kum havuzu ve korku tepkisi

- [ ] Lisansı serbest görsellerden ve videolardan oluşan yerel bir feed
- [ ] Tam kapalı döngü: feed → gözler → beyin → gövde + eylem → feed
- [ ] Karar günlüğü (her eylemin nöral gerekçesi)
- [ ] Tekrarlanabilirlik testi (aynı seed → aynı davranış)
- [ ] Zamansal görme: videolar ve kaydırma hareketi (Z-25)
- [ ] Korku testi: yaklaşan nesne → LPLC2/LC4 → dev lif → sıçrama

**Bitiş:**
- Sinek sahte feed'de saatlerce çökmeden "geziniyor".
- Her eylemi açıklanabiliyor.
- Kaçış tepkisi yalnızca sineğin kendi devresinden doğuyor.

## Faz 8 — Instagram bağlantısı

- [ ] Playwright ile tarayıcı bağlantısı (K-006)
- [ ] Kalıcı oturum (giriş kullanıcı tarafından elle yapılır)
- [ ] Güvenlik valisi: hız sınırları, doğrulama algılama → durdur ve bildir
- [ ] Kuru çalıştırma modu: eylemleri loglar ama uygulamaz
- [ ] Gerçek hesapta düşük limitli ilk oturum

**Bitiş:** Sinek gerçek feed'de bir oturumu sorunsuz tamamlıyor.

## Faz 9 — İçerik üretimi

- [ ] Görsel üretimi (nöral portre ve gövdenin gerçek yürüyüş izinden yürüyüş resmi)
- [ ] Caption üretimi (seçilen yöntem)
- [ ] Paylaşım zamanlaması (P1 birikimi)
- [ ] İçerik vetosu (yasaklı kelimeler)

**Bitiş:** Sinek ilk postunu kendi kararıyla paylaşıyor.

## Faz 10 — Öğrenme ve uzun dönem çalışma

- [ ] Mantar gövdesi plastisitesi (dopamin kapılı)
- [ ] Beyin durumunun (homeostaz eşikleri dahil) oturumlar arası kalıcılığı
- [ ] Zamanlanmış oturumlar
- [ ] "Sinek günlüğü": feed nasıl değişti, sinek neyi öğrendi

**Bitiş:** Haftalık raporlar feed'in ve sineğin tercihlerinin birlikte değiştiğini gösteriyor.
