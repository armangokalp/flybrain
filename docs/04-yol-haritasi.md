# 04 — Yol Haritası

Her faz, bitiş kriterleri sağlanmadan kapanmaz. Gerçek Instagram hesabına ilk dokunuş **Faz 6**'da olacak; o zamana kadar her şey yerelde test edilir.

## Faz 0 — Araştırma ve mimari 🟡

- [x] Veri setinin güncel durumunu araştırmak (MaleCNS v1.0, Eylül 2026)
- [x] Referans simülasyon modellerini belirlemek (Shiu ve ark. LIF)
- [x] Mimari taslağı, ilkeler ve zorluklar belgeleri
- [ ] Açık tasarım kararlarının kullanıcıyla netleştirilmesi (bkz. [kararlar.md](kararlar.md))

**Bitiş:** Mimari onaylandı, veri indirme izni alındı.

## Faz 1 — Konnektom veri hattı

- [ ] Python ortamı (`pyproject.toml`, sanal ortam)
- [ ] İndirme betiği: anotasyonlar, nörotransmitterler, bağlantı ağırlıkları
- [ ] Nöron filtresi (yalnızca izlenmiş/anotasyonlu gövdeler)
- [ ] Seyrek ağırlık matrisi + işaretler → önbellek (`data/cache/`)
- [ ] Veri keşif raporu: aday duyu ve motor nöronlarının tabloda gerçekten olup olmadığı ([02-mimari.md](02-mimari.md) tablolarının doğrulanması)

**Bitiş:** `load_connectome()` birkaç saniyede matrisi yüklüyor; aday nöron listesi doğrulanmış.

## Faz 2 — Simülasyon çekirdeği

- [ ] LIF motoru (olay güdümlü, seyrek)
- [ ] Performans ölçümü (simülasyon saniyesi başına duvar saati)
- [ ] **Doğrulama:** şeker tat nöronlarının uyarılması MN9'u ateşliyor mu? (Shiu ve ark. sonucunun MaleCNS'de tekrarı)
- [ ] Taban aktivite ve kararlılık testleri (sessizlik / epilepsi)

**Bitiş:** Doğrulama deneyi yayınlanmış sonuçla nitel olarak uyuşuyor; 500 ms'lik bir karar penceresi makul sürede hesaplanıyor.

## Faz 3 — Duyu kodlayıcıları

- [ ] Görme: görsel → altıgen ommatidyum ızgarası → fotoreseptör ateşleme hızları
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

- [ ] Seçilen bağlantı yöntemi (karar bekliyor)
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
