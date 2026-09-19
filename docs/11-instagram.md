# 11 — Instagram Bağlantısı (Faz 8)

Kararlar: K-006, K-007, K-034. Zorluklar: Z-10, Z-11, Z-13, Z-36, Z-37. Kod: `flybrain/insta/`.

## 1. Zincir

```
tarayıcı (telefon görünümü, karanlık mod)
   │ ekran görüntüsü
   ▼
sineğin telefonu (solarak geçiş, K-030) ──► gözler ──► beyin ──► kas kanalları ──► karar
                                                                                    │
                                    güvenlik valisi (yalnızca veto, K-007) ◄─────────┘
                                                   │ izin verilirse
                                                   ▼
                                    tarayıcı düğmeye basar → sonuç doğrulanır
                                                   │
                                    eylem sonrası ekran görüntüsü ──► sineğin telefonu
```

Sinek gerçek tarayıcıyı görmez; yalnızca sahnesindeki telefonu görür. Bu yüzden **kaydırma
sineği korkutmaz**: tarayıcı kaydırmayı solma sürerken perde arkasında yapar (Z-35, K-030).
Kalan risk videolarda ve çoklu görsellerde; oradaki sert değişimler "anında geçiş"e benziyor
(12 denemede 1–2 kaçış, K-030 tablosu).

## 2. Tarayıcı (`insta/browser.py`)

| Ayar | Değer | Neden |
|---|---|---|
| Profil | `browser-profile/` (gitignore'da) | Giriş kullanıcıya ait; kod şifre görmez |
| Görüntü alanı | 390 × 844 (19,5:9) | Sineğin telefonuyla aynı oran; story yükleme yalnızca mobil düzende |
| Ölçek | 2× | Ekran görüntüsü 780 × 1688; ekrana 540 × 1170 olarak küçültülüyor |
| Tema | karanlık | Solarak geçişin ölçüldüğü tema (K-030) |
| Hareket | `prefers-reduced-motion` | Site kendi animasyonlarını kısarsa sinek daha az ani değişim görür |
| Pencere | görünür | Otomasyon izlenebilsin, doğrulama çıkarsa kullanıcı çözebilsin (Z-11) |

## 3. Akış ve eylemler (`insta/feed.py`)

- **Okuma:** Her post bir `article`. Alınanlar: kullanıcı adı, açıklama (koku olur), bağlantı,
  video mu, ekran görüntüsü.
- **Eylem sırası:** valiye sor → bakılan postu **bağlantısıyla** bul → düğmeyi bul → tıkla →
  **durumu yeniden oku** → görünen öteki postların durumunu karşılaştır → kaydet. Düğmenin
  etiketi değişmediyse eylem "başarısız" yazılır; sessiz başarısızlık yok.
- **Hedef:** Eylemler postu yalnızca bağlantısıyla bulur, indeksle asla (Z-45): Instagram akışın
  başından post siliyor ve indeks başka bir posta kayıyor. Post sayfada yoksa hiçbir şeye
  dokunulmaz. Yorum sayfası bakılan postun değilse hiçbir şey yazılmaz; gönderilen yorumun
  sayfada göründüğü doğrulanır.
- **Yanlış post:** Beğeni hedef dışında bir postu değiştirdiyse kayda `sapma` olarak geçer, iz
  hız sınırına sayılır ve oturum durur (Z-44, Z-45).
- **Etiketler:** Düğmeler erişilebilirlik etiketinden bulunuyor; arayüz dili hesaba göre
  değiştiği için Türkçe ve İngilizce birlikte aranıyor (Z-36).

| Sineğin kararı | Instagram'da karşılığı |
|---|---|
| beğen / kaydet | kalp / yer imi düğmesi |
| takip | takip düğmesi |
| yorum | yorum kutusu; metni sinek koklayarak seçiyor (K-041) |
| ileri, geri, sekme, tımar, ilgi kaybı | yok; yalnızca gövde hareketi ve akışta ilerleme |
| çıkış | bağlı sinekte çırpınma; post bitmez, sinek bakmaya devam eder (K-040) |

## 4. Güvenlik valisi (`insta/governor.py`)

- **Hız sınırları (ısınma):** saatlik/günlük üst sınırlar ve eylemler arası en az bekleme.
  Sayaçlar `runs/insta/eylemler.jsonl` dosyasında; oturumlar arasında korunuyor.

  | | beğen | kaydet | takip | yorum | paylaş | story |
  |---|---|---|---|---|---|---|
  | saatlik | 20 | 10 | 3 | 2 | 1 | 2 |
  | günlük | 100 | 50 | 10 | 8 | 2 | 4 |

- **İçerik vetosu:** Yorumda yasaklı kelime varsa eylem uygulanmaz (`insta/yasakli.txt`, Z-13).
- **Doğrulama algılama:** Adres `/challenge/`, `/accounts/suspended` gibi bir sayfaya düşerse ya
  da oturum kapanırsa oturum durur. Sistem doğrulamayı atlatmaya **çalışmaz** (Z-11).
- **Vali eylem seçmez.** Engellenen eylem de gerekçesiyle kaydedilir (K-007).

## 5. Sıra: sahte akış → kuru çalıştırma → gerçek

0. **Giriş (bir kez, kullanıcı yapar):** `python -m flybrain.insta.login` tarayıcıyı açar ve
   oturum çerezi oluşana kadar bekler. Şifre koda girilmez, okunmaz, saklanmaz.
1. **Yerel sahte akış** (`tests/sahte_akis.html`): Gerçek Instagram değil; yalnızca düğme bulma,
   tıklama ve doğrulama mantığını sınayan yerel bir test sayfası. Bütün döngü burada çalışıyor:
   ```bash
   python -m flybrain.insta.session --posts 3 --sahte --gercek
   ```
2. **Kuru çalıştırma:** Gerçek hesapta; sinek karar verir, eylemler kaydedilir ama tıklanmaz.
   ```bash
   python -m flybrain.insta.session --posts 20 --izle     # --izle: canlı yayın
   ```
3. **Gerçek oturum:** `--gercek` ile, düşük limitlerle ve kullanıcı onayıyla.

## 6. Ölçüm: oturum başlangıcında kaçış

İlk oturumlarda sinek her seferinde ilk pencerede "çıkış" verip uçup gitti. Ekranın karanlık
olmasından sanıldı; ölçüm başka şey gösterdi.

**Ekranın içeriği değil:** Aynı protokolde sentetik post, karartılmış sürümleri (×0,6, ×0,35,
×0,2) ve gerçek Instagram ekranı — hepsinde kaçış kanalı 0,00 Hz.

**Yerleştirme sonrası bekleme:** Deneyci sineği yerleştirdikten sonra posta geçmeden önceki
bekleme belirleyici.

| Bekleme | Pencere 0 kaçış | Göğüs hareketi | Diklik |
|---|---|---|---|
| 500 ms | 6,97 Hz | 3,60 mm (sıçrama) | 0,10 (devrildi) |
| 2000 ms | 0,00 Hz | 0,15 mm | 0,99 |

Oturum yerleştirmeden sonra **2 sn** bekliyor (`insta/session.py`, `SETTLE_MS`). Sonrasında sahte
akışta üç post sorunsuz geçti. Aynı kısa bekleme yerel oturumlarda da (Faz 6) kullanılıyordu;
oradaki erken "çıkış" kararlarının bir kısmı bundan olabilir — ölçülmedi.

## 7. Gerçek hesapta ilk kuru çalıştırmalar (2026-09-17)

Giriş kullanıcı tarafından yapıldı; aşağıdaki oturumların hiçbirinde düğmeye basılmadı.

**Arayüz doğrulandı (Z-36):** Gerçek sayfadaki etiketler `Like`, `Comment`, `Save`, `Follow`;
kodun aradıklarıyla aynı. Post bir `article`, kullanıcı adı ilk profil bağlantısından, açıklama
ise postun metin bloğundan okunuyor.

**Üç hata bulundu ve düzeltildi:**

| Hata | Belirti | Çözüm |
|---|---|---|
| Giriş sonrası kutu | Sinek akış yerine "Save your login info?" kutusunu gördü | Kutular kapatılıyor; yalnızca reddeden düğmeye basılıyor |
| Açıklama okuması | Açıklama "89K", "Suggested for you" çıkıyordu | Sayaç, öneri ve zaman satırları eleniyor |
| Akışta ilerleme | 10. postta "yüklenmedi" hatası | Sıradaki post indeksle değil **bağlantısıyla** bulunuyor; akış gerektikçe yükleniyor |

**Dördüncü hata — sinek fotoğrafı görmüyordu.** Sanal telefon zemine gömülü; sinek ekranın alt
bölümünü görüyor ve yerel akışta bakılan postun görseli tam oraya yerleştiriliyor (body/phone.py).
Gerçek sayfada post ekranın üstüne hizalanınca sineğin baktığı bölgeye görsel değil, beğeni sayısı
ve açıklama satırları denk geliyordu. Artık tarayıcı, postun **en büyük görselinin alt kenarını**
gezinme çubuğunun üstüne hizalıyor (`InstaFeed._align`); ölçülen görsel yüksekliği 487–520 piksel,
sineğin bandına oturuyor.

**Kaçış (K-037):** Sinek gerçek fotoğraflarda sık "çıkış" veriyor; geçiş süresi uzatılarak
azaltıldı (ölçüm tablosu K-037'de). Uçup giden sineği deneyci geri getiriyor.

**20 postluk oturum** (geçiş 1200 ms, kuru çalıştırma, `runs/insta-kuru6`):

| Karar | Sayı |
|---|---|
| ilgi kaybı | 9 |
| beğeni | 3 |
| ileri | 3 |
| çıkış (uçup gitme) | 4 |
| tımar | 1 |

Süre 131 sn (simülasyon ~2,2 dakika). Beğeni kararlarının üçü de uygulanmadı; kuru çalıştırmada
yalnızca kaydedildi.

## 8. Beşinci hata — sinek postu görüyordu ama yarısını göremiyordu

Dördüncü düzeltmeden sonra da bir şey tutmuyordu. Bu kez ekran görüntüsü kaydına değil
**göz kaydına** (`runs/*/gozler.mp4`) bakıldı: sineğin ne gördüğü, kodun ne gösterdiğini
sandığından farklıydı. Dört ayrı hata çıktı; ayrıntısı [Z-38](03-zorluklar.md#z-38).

En sinsi olanı ikincisiydi: Instagram'ın web sürümü sayfanın altına "Use the app" bandı koyuyor
(y 759–794). Band tam olarak postun hizalandığı yeri, yani **sineğin baktığı şeridi** örtüyordu;
sinek fotoğrafın alt kenarı yerine parlak mavi bir çizgi görüyordu. Gerçek uygulamada böyle bir
band yok — yani sineğin dünyasında da olmamalı. Kapatılıyor.

Ölçüm (gerçek akış, 8 post): görselin alt kenarının hedeften sapması ≤ 0,5 piksel, tekrar eden
post yok, band yok.

## 9. Açık konular

- **Z-36 · Arayüz etiketleri:** Düğme etiketleri gerçek oturumda doğrulanmadı; Instagram arayüzü
  değişirse eylem "başarısız" olarak kaydedilir (sessizce yanlış bir düğmeye basılmaz).
- **Z-37 · Video zamanı:** Tarayıcıdaki video gerçek zamanda oynar, simülasyon ~3 kat yavaştır.
  Reels'in kareleri tarayıcıdan toplanıp sineğe simülasyon zamanıyla oynatılıyor (`grab_video`).
- **Z-39 · Görmek ve kaçmak çelişiyor:** Postun kadraja sığması ile kaçışın çalışması aynı açıya
  ters yönde bağlı. Ekran dünyada sabit bir nesneye çevrildi; mesafeyi sinek seçiyor (K-038).
  Çelişki çözülmedi, kök neden Z-25.
- **Bildirimler:** Sineğin kendi postlarına gelen beğeni ve yeni takipçiler ödül nöronlarına
  bağlanacak (`senses/reward.py`); Instagram'dan okunması henüz yazılmadı.
- **Yorum metni:** K-041 ile açıldı; metin yalnızca koklanan kelimelerden geliyor, duygu
  bileşeni Z-40'ta düştü. Bildirimler ödül nöronlarına bağlanınca (Faz 9) yeniden bakılacak.
- **Geçiş kaldırıldı (K-039):** Yeni sahnede solmanın ölçülebilir faydası kalmadı (11 çiftte
  kaçış anında 3, 1200 ms'de 3). Ekran artık Instagram'daki gibi anında değişiyor. Ölçüm
  tekrarlanabilir: `python -m flybrain.experiments.gecis --postlar 12`; kaydedilmiş bir
  oturumdan da beslenebiliyor (`--kayittan runs/<ad>`, tarayıcı açılmaz).
- **Paylaşım:** Post Faz 9'da (K-004, K-005), story oturum videosundan (K-035).
