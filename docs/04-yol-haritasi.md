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

Ayrıntı: [09-govde.md](09-govde.md). Kararlar: K-019–K-032.

- [x] Gövde kütüphanesi (FlyGym 2.1, NeuroMechFly): 126 eklem serbestlik derecesi, fizik gerçek zamandan hızlı
- [x] Yürüme ritmi yoklaması: DNg100 → ritim çekirdeği → bacak motor nöronları (Z-22)
- [x] Ölçülmüş elektriksel sinapslar: dev lif → TTMn, PSI (K-023)
- [x] Motor nöron → kas → eklem tablosu (bacaklar, baş, hortum, kanatlar, karın, sıçrama) ve kas modeli (Z-24, ilk sürüm)
- [x] Gövdeden beyne his, ilk sürüm: uyluk kordotonal organı ve kıl plakaları, 389 nöron (K-024). Yük, zemin teması, baş konumu eksik (Z-32)
- [x] Sinir kordonu hız modeli (K-025, deneysel): Pugliese ve ark. ön bacak ritmi yeniden üretildi, altı bacağa genişletildi, LIF beyinle melez
- [ ] Yürüme: hız modelinde motor çıktı düşük, doyum ve duyu kazancı kalibre değil (Z-33) — ertelendi (K-026)
- [x] Sineğin gözleriyle görme: başa bağlı kameralar → konnektom göz kolonları, zamansal uyum (K-027)
- [x] Sahne: serbest sinek ve onu izleyen dikey, kavisli telefon ekranı; Instagram benzeri akış, koyu tema, sonraki posta solarak geçiş (K-021, K-028, K-030)
- [x] Yaklaşan nesne → kaçış: ekranda büyüyen disk dev lifi açık temada %91–96, koyu temada %77 ateşletiyor; gövdeli görme kazancı 125 Hz (K-029, K-030, Z-25)
- [ ] Dinlenen sineğin kendi hareketinden gelen kendiliğinden kaçışlar (~17 sn'de bir, Z-34)
- [x] Post geçişinde kaçış: kaydırma her seferinde kaçış tetikliyordu; geçiş solma ve koyu temayla çözüldü (Z-35, K-030)
- [x] Kapalı döngü (beyin + gövde + görme + ekran) ve hız iyileştirmesi (Z-21): gerçek zamanın 2,95–3,25 katı yavaş (4 iş parçacığı; önce ~4,5)
- [x] Neden–sonuç testleri: MN9 → hortum ✅, dev lif → sıçrama ✅ (K-023), DNg100 → bacaklar kıpırdıyor ama yürüme yok, şeker → kısmi (Z-30)
- [x] Gövdeli sinekte kararlar: ayrı kalibrasyon, düşen sineği deneyci yeniden yerleştiriyor (K-031)
- [x] Nöral karar ile gövde hareketinin örtüşme ölçümü ve gövde onayı şartı (K-020, K-032, Z-27)
- [ ] İlgi kaybında görünür bir hareket yok; sekme ve önceki post onaylı kuralda neredeyse hiç seçilmiyor; uzun oturumda oranlar etkinlik dönemleriyle salınıyor (Z-27)
- [ ] Düşen sineğin kendi kendine doğrulması (Z-26)

**Bitiş:**
- Beyin sessizken gövde hareketsiz.
- Uyarılan her motor devresi, beklenen gövde bölgesini hareket ettiriyor.
- Kapalı döngü gerçek zamanın en fazla 3 katı yavaşlıkta çalışıyor.

## Faz 6 — Görselleştirme ve kayıt

Ayrıntı: [10-gorsellestirme.md](10-gorsellestirme.md). Karar: K-033.

- [x] Oturum kaydı: spike'lar (1 ms), gövde durumu ve telefon ekranının konumu (5 ms), sineğin göz görüntüsü, ekran, kararlar
- [x] Yerel izleme paneli (three.js), senkron görünümler:
  - 3D sinek ve telefon ekranı
  - 3D sinir sistemi (165.122 nöron, soma konumlarında; %15'inin konumu yaklaşık)
  - sineğin gördüğü
  - Instagram ekranı
  - karar günlüğü
- [x] Geriye izleme: karara ya da gövde parçasına tıklayınca ilgili motor nöronlar ve spike sayıları
- [x] Kayıttan gerçek hızda ve ağır çekimde oynatma
- [x] Canlı mod: simülasyon sürerken tarayıcıdan izleme, ağır çekim etiketli (`viz/live.py`, Z-28)
- [ ] Uzun oturumlar için spike verisinin parçalı yüklenmesi
- [ ] Beyin bölgesi yüzeyleri ve önemli nöronların şekilleri (indirme için ayrıca izin istenecek)
- [x] Paylaşılabilir video dışa aktarımı (gerçek hız ya da etiketli ağır çekim)

**Bitiş:** Bir oturum baştan sona izlenebiliyor. Görülen her hareket, o anda ateşleyen motor nöronlara kadar geriye doğru izlenebiliyor.

## Faz 7 — Yerel kum havuzu ve korku tepkisi

- [ ] Lisansı serbest görsellerden ve videolardan oluşan yerel bir feed
- [ ] Tam kapalı döngü: feed → gözler → beyin → gövde + eylem → feed
- [ ] Karar günlüğü (her eylemin nöral gerekçesi)
- [ ] Tekrarlanabilirlik testi (aynı seed → aynı davranış)
- [ ] Zamansal görme: videolar ve kaydırma hareketi (Z-25)
- [ ] Korku testi: yaklaşan nesne → LPLC2/LC4 → dev lif → sıçrama
- [ ] Kaçışın yaklaşmaya özgüllüğü: model kararmaya da yaklaşma kadar güçlü kaçıyor; gerçek LPLC2 kaçmıyor. Hareket yönü hesabı (T4/T5) ve kontroller (Z-25)

**Bitiş:**
- Sinek sahte feed'de saatlerce çökmeden "geziniyor".
- Her eylemi açıklanabiliyor.
- Kaçış tepkisi yalnızca sineğin kendi devresinden doğuyor.

## Faz 8 — Instagram bağlantısı

- [x] Playwright ile tarayıcı bağlantısı: telefon görünümü, karanlık mod (K-006). Animasyonlar açık: sinek kendi beğenisinin kalbini görüyor (2026-09-18, kullanıcı kararı)
- [x] Kalıcı oturum (giriş kullanıcı tarafından elle yapılır; kod şifre görmez)
- [x] Ekran görüntüsü → sineğin telefonu, solarak geçiş; kaydırma perde arkasında (K-034)
- [x] Eylemler: beğen, kaydet, takip, yorum — her biri tıklama sonrası doğrulanıyor
- [x] Güvenlik valisi: hız sınırları, yasaklı kelime vetosu, doğrulama algılama → durdur ve bildir
- [x] Kuru çalıştırma modu: eylemleri loglar ama uygulamaz
- [x] Yerel sahte akışta uçtan uca deneme (`tests/sahte_akis.html`)
- [ ] Yorum metni: duygu okuması + koklayarak kelime seçimi (K-036)
- [ ] Bildirimler (gelen beğeni, yeni takipçi) → ödül nöronları (`senses/reward.py`)
- [x] Gerçek hesapta kuru çalıştırma; arayüz etiketleri doğrulandı (Z-36)
- [x] Gerçek hesapta düşük limitli ilk oturum: 1 beğeni uygulandı ve doğrulandı (2026-09-17)
- [x] Akış hataları: bildirim sayfası, "Use the app" bandı, hiza, tekrar eden post (Z-38)
- [x] Reels oynuyor: kareler tarayıcıdan toplanıp simülasyon zamanıyla gösteriliyor (Z-37)
- [x] Telefon dünyada sabit nesne; mesafe sineğin kararı (K-038) — kalibrasyonlar yenilendi
- [ ] Postlar arası geçiş süresinin yeni sahnede yeniden ölçülmesi (K-037 eski düzende ölçüldü)

**Bitiş:** Sinek gerçek feed'de bir oturumu sorunsuz tamamlıyor.

## Faz 9 — İçerik üretimi

- [ ] Görsel üretimi (nöral portre ve gövdenin gerçek yürüyüş izinden yürüyüş resmi)
- [ ] Caption üretimi (seçilen yöntem)
- [ ] Story: sineğin kendi oturum videosundan kesit (K-035)
- [ ] Paylaşım zamanlaması (P1 birikimi); story için de kural
- [x] İçerik vetosu (yasaklı kelimeler; `insta/yasakli.txt`, Faz 8'de yazıldı)

**Bitiş:** Sinek ilk postunu ve ilk story'sini kendi kararıyla paylaşıyor.

## Faz 10 — Öğrenme ve uzun dönem çalışma

- [ ] Mantar gövdesi plastisitesi (dopamin kapılı)
- [ ] Beyin durumunun (homeostaz eşikleri dahil) oturumlar arası kalıcılığı
- [ ] Zamanlanmış oturumlar
- [ ] "Sinek günlüğü": feed nasıl değişti, sinek neyi öğrendi

**Bitiş:** Haftalık raporlar feed'in ve sineğin tercihlerinin birlikte değiştiğini gösteriyor.
