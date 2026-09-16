# 04 — Yol Haritası

Her faz, bitiş kriterleri sağlanmadan kapanmaz. Gerçek Instagram hesabına ilk dokunuş **Faz 6**'da olacak; o zamana kadar her şey yerelde test edilir.

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

## Faz 3 — Duyu kodlayıcıları

- [ ] Görme: görsel → `hex1 × hex2` kolon ızgarası → giriş nöronları (fotoreseptörlerin ketleyici olması nedeniyle yöntem Z-02'ye göre seçilecek)
- [ ] Fotoreseptör kolonlarının bağlantıdan çıkarılması (Z-09)
- [ ] Katman katman sinyal yayılımı analizi (Z-02)
- [ ] Koku: kelime → ORN kombinasyonu (sabit hash)
- [ ] Ödül/ceza: bildirim → PAM/PPL1 uyarımı

**Bitiş:** Farklı görseller inen nöronlarda ayırt edilebilir aktivite desenleri üretiyor.

## Faz 4 — Motor kod çözücü

- [ ] Motor havuzlarının tanımı (doğrulanmış nöron listeleriyle)
- [ ] Kalibrasyon protokolü (nötr uyaran → eşikler)
- [ ] Eylem seçimi ve "bakmaya devam" mantığı
- [ ] "Beğen" eşlemesinin kararlaştırılması (Z-04)

**Bitiş:** Gri ekranda hiçbir eylem tetiklenmiyor; gerçek görsellerde eylem dağılımı dejenere değil (tek bir eylem baskın değil).

## Faz 5 — Yerel kum havuzu (sahte feed)

- [ ] Lisansı serbest görsellerden oluşan yerel bir feed
- [ ] Tam kapalı döngü: feed → beyin → eylem → feed
- [ ] Karar günlüğü (her eylemin nöral gerekçesi)
- [ ] Tekrarlanabilirlik testi (aynı seed → aynı davranış)

**Bitiş:** Sinek sahte feed'de saatlerce çökmeden "geziniyor" ve her eylemi açıklanabiliyor.

## Faz 6 — Instagram bağlantısı

- [ ] Playwright ile tarayıcı bağlantısı (K-006)
- [ ] Kalıcı oturum (giriş kullanıcı tarafından elle yapılır)
- [ ] Güvenlik valisi: hız sınırları, doğrulama algılama → durdur ve bildir
- [ ] Kuru çalıştırma modu: eylemleri loglar ama uygulamaz
- [ ] Gerçek hesapta düşük limitli ilk oturum

**Bitiş:** Sinek gerçek feed'de bir oturumu sorunsuz tamamlıyor.

## Faz 7 — İçerik üretimi

- [ ] Görsel üretimi (seçilen yöntem)
- [ ] Caption üretimi (seçilen yöntem)
- [ ] Paylaşım zamanlaması (P1 birikimi)
- [ ] İçerik vetosu (yasaklı kelimeler)

**Bitiş:** Sinek ilk postunu kendi kararıyla paylaşıyor.

## Faz 8 — Öğrenme ve uzun dönem çalışma

- [ ] Mantar gövdesi plastisitesi (dopamin kapılı)
- [ ] Beyin durumunun oturumlar arası kalıcılığı
- [ ] Zamanlanmış oturumlar
- [ ] "Sinek günlüğü" paneli: feed nasıl değişti, sinek neyi öğrendi

**Bitiş:** Haftalık raporlar feed'in ve sineğin tercihlerinin birlikte değiştiğini gösteriyor.
