# 10 — Görselleştirme ve Kayıt (Faz 6)

Karar: K-033. Zorluk: Z-28. Kod: `flybrain/viz/`.

## 1. Neden önce kayıt?

- **Döngü yavaş.** Kapalı döngü gerçek zamanın ~3 katı yavaş (Z-21). Kayıt sırasında video da kodlandığı için ~4 kat; 44 sn'lik bir oturum 3 dakikada kaydediliyor.
- **Kayıt izlemeyi ayırıyor.** Oturum bir kez kaydedilir, sonra istenen hızda ve açıdan izlenir.
- **Kayıt tanıktır.** Panelde görülen her şey kayıttan gelir; fizik ya da beyin yeniden çalıştırılmaz.

```bash
python -m flybrain.viz.session --posts 40 --seed 8003 --out runs/oturum-ilk   # kayıt
python -m flybrain.viz.serve runs/oturum-ilk                                   # panel: http://127.0.0.1:8765/
python -m flybrain.viz.video runs/oturum-ilk --son 20                          # paylaşılabilir video
```

## 2. Oturum kaydı (`viz/record.py`)

`EmbodiedFly.recorder` her 1 ms'lik adımın sonunda, fizikten ve deneyci müdahalesinden sonra çağrılır. `FeedViewer` post başlangıçlarını ve kararları olay olarak ekler.

| Dosya | İçerik | 44 sn'lik oturumda |
|---|---|---|
| `spikes.npz` | her milisaniyede ateşleyen nöronlar (indeks) | 6,8 milyon spike, 11 MB |
| `govde.npz` | 5 ms'de bir durum vektörü (133 sayı), telefon ekranının konumu, deneyci tutuyor mu | 4 MB |
| `gozler.mp4` | sineğin iki gözünün kamera görüntüsü, 30 kare/sn | 5 MB |
| `ekran.mp4` | telefon ekranı, 30 kare/sn | 9 MB |
| `olaylar.json` | post başlangıcı, karar (gerekçe, z-skorları, gövde ölçüleri), yeniden yerleştirme | 29 KB |

**Veri hacmi (Z-28):**
- Saniyede ~150 bin spike atılıyor; 16 bin nöron en az bir kez ateşliyor.
- 5 dakikalık bir oturum ~200 MB tutar.

**Doğrulama** (`tests/test_viz.py`):
- **Spike'lar:** Kayıttaki spike'lar, karar okumasının kullandığı spike sayaçlarıyla birebir aynı.
- **Gövde:** Kayıttan kurulan gövde ve telefon ekranı, sineğin son duruşuyla aynı.
- **Video:** Her kayıt zamanı için bir video karesi var.

**Bulunan hata:** Telefon ekranı fizik dışı (mocap) bir gövde; konumu durum vektöründe değil. İlk kayıt sürümü ekranın konumunu tutmuyordu ve panelde telefon başlangıç yerinde kalıyordu. Artık ayrıca kaydediliyor.

## 3. Panel (`viz/web/`, `viz/serve.py`)

Yerel web sayfası; three.js ile çiziliyor (K-033). Sunucu yalnızca `127.0.0.1`'de dinliyor, kayıt dizininin dışına çıkılamıyor; videoda ileri geri atlamak için bayt aralığı istekleri destekleniyor.

| Görünüm | İçerik |
|---|---|
| Sinek | Kayıttaki duruşlardan 3D sinek; arkasında kavisli telefon ekranı, kaydedilen ekran videosuyla. Kamera sineği izler, fareyle döner. |
| Sinir sistemi | 165.122 nöron, soma konumlarında, sınıfa göre sönük renkli. Son ~60 ms'de spike atanlar parlak (üstel sönüm). |
| Gözler, telefon | Kayıttaki videolar, zamana kilitli. |
| Kararlar | Günlük: zaman, post, eylem, bakma süresi. Üstte o anki durum ("bakıyor…" ya da son karar ve gerekçesi). |
| Geriye izleme | Bir karara ya da gövde parçasına tıklanınca ilgili motor nöronlar (aşağıda). |

**Zaman çizgisi:** Kararlar eylem renginde, yeniden yerleştirmeler beyaz işaretli. Hız 0,1×–2×; boşluk tuşu oynatır, oklar kare ya da saniye atlar.

### 3.1 Geriye izleme

- **Karara tıklamak:**
  - Oynatma post başına gider.
  - Kararı veren kanalın nöronları beyinde işaretlenir.
  - Post başından karara kadar en çok ateşleyen nöronlar tipleriyle listelenir.
  - Bu nöronların kaslarıyla hareket eden gövde parçaları vurgulanır.
  - Örnek (post 3, sonraki post): 381 bacak motor nöronundan 4'ü ateşledi (tibia fleksörü 8, plevral remotor 7, sternotrokanter 4, femur redüktörü 1 spike).
- **Gövde parçasına tıklamak:**
  - O parçayı hareket ettiren kaslar ve motor nöronları gelir. Kası olmayan parçalar (tarsus uçları, antenler) kaslı en yakın atalarına bağlanır.
  - Son 0,5 sn'deki spike sayıları listelenir; nöronlar beyinde işaretlenir.
  - Göğsü ve halterleri doğrudan hareket ettiren kas yok; panel bunu söyler.
- **Eşleme:** Bir eklemin adındaki ikinci parça, eklemin hareket ettirdiği gövde parçasıdır (ör. `lf_trochanterfemur-lf_tibia-pitch` → `lf_tibia`). Kas → eklem tablosu Faz 5'ten (`body/muscles.py`).

### 3.2 Nöron konumları

- **Kaynak:** MaleCNS soma konumları (8 nm voksel → µm).
- **Eksik konumlar:** 25.098 nöronun (%15) soma konumu yok. Çoğu duyu nöronu (vnc 6.363, cb 4.868, ol 4.086) ya da optik lob iç nöronu (7.708). `tosomaLocation` yalnızca 976'sında var.
- **VARSAYIM:** Bu nöronların konumu, bağlantılı oldukları nöronların konumlarının sinaps sayısıyla ağırlıklı ortalaması. Panelde "konumu yaklaşık nöronlar" seçeneğiyle gizlenebiliyorlar.
- Gerçek konumlar için iskelet ya da sinaps verisi indirmek gerekir; bu ayrıca izin ister.

### 3.3 Karşılaşılan sorunlar

- **Kamera:** Telefonun arkası sineği kapatıyordu. Kamera sineğin arkasına ve yanına, ekrana bakacak şekilde yerleştirildi; zeminin altına inemiyor.
- **Ekran dokusu:** MuJoCo'da görüntünün ilk satırı ekranın üst kenarında. three.js'te doku çevrilmeden (`flipY = false`) doğru yönde çıkıyor. İlk bakışta başlık görünmediği için ters sanıldı; oysa ekranın üstü kadrajın dışındaydı.
- **Beyin parlaklığı:** 165 bin nokta eklemeli karışımla toplanınca optik loblar beyaza doyuyordu. İki katmana ayrıldı: sönük sınıf renkleri (normal karışım) ve üstte parlak ateşleyen nöronlar.
- **Sinek renkleri:** Parçaların MuJoCo'daki dokuları küp dokusu ve doku koordinatı yok. Her parça dokusunun ortalama rengiyle boyanıyor; dokular zaten neredeyse düz renk.
- **Ekran görüntüsü aracı:** Tarayıcı araçları video katmanlarını çoğu zaman yakalamıyor; videoların doluluğu piksel okumasıyla doğrulandı.

## 4. Paylaşılabilir video (`viz/video.py`)

- **Kare (1280 × 720):**
  - sinek ve telefon ekranı (MuJoCo, kaydedilen ekran görüntüsüyle);
  - sinir sisteminin iki boyutlu izdüşümü (beyin üstte, sinir kordonu altta);
  - gözler, telefon, son karar ve gerekçesi, son beş karar.
- **Etiketler:** Zaman ve hız her karede yazılı; hız 1'den küçükse "ağır çekim" etiketi var (Z-28). "Deneyci sineği tutuyor" durumu da yazılıyor.

**Ölçüm (oturum-ilk):**

| Video | Süre | Üretim süresi | Boyut |
|---|---|---|---|
| ilk 20 sn, gerçek hız | 20 sn | 16 sn | 11 MB |
| 10–13. sn, 0,25× ağır çekim | 12 sn | 9 sn | 4 MB |

- **Emojiler:** Caption'lardaki emojiler Arial'de yok; renkli emoji yazı tipiyle ayrıca çiziliyor.
- **Telefon ekranı:** MuJoCo'da kaydedilen ekran görüntüsüyle doku olarak güncelleniyor. Kamera sineğin arkasında, ekranın iç yüzünü görüyor.

## 5. Sıradakiler

- **Canlı mod:** Simülasyon sürerken panelin kaydı parça parça okuması, açıkça "ağır çekim" etiketiyle (Z-28).
- **Uzun oturumlar:** Spike dosyasının parçalı yüklenmesi (ham spike dizisi 44 sn için 27 MB, 5 dakikada ~185 MB).
- **Beyin bölgeleri:** Bölge yüzeyleri ve önemli nöronların şekilleri (indirme izni gerekir).
- **Faz 7:** Yerel feed. Panel aynı kayıt biçimini kullanacak.
