# 03 — Zorluklar ve Çözüm Yolları

Bu belge yaşayan bir belgedir. Yeni bir sorunla karşılaştıkça buraya eklenir, çözüldükçe durumu güncellenir.

Durum etiketleri: 🔴 açık · 🟡 üzerinde çalışılıyor · 🟢 çözüldü

---

## Bilimsel zorluklar

### Z-01 · Konnektom kabloları veriyor, sinaps güçlerini vermiyor 🔴

Haritada hangi nöronun hangisine kaç sinapsla bağlandığı var. Sinapsın ne kadar güçlü olduğu ve bazı durumlarda uyarıcı mı ketleyici mi olduğu yok.

**Çözüm yolu:** Shiu ve ark. modelinin varsayımını kullanıyoruz: her sinaps eşit ağırlıkta, işaret ise nörotransmitter tahmininden geliyor. Bu model tat devrelerinde deneysel olarak doğrulandı. Aynı doğrulamayı MaleCNS üzerinde tekrarlayacağız (şeker nöronlarını uyar, MN9 ateşliyor mu bak). Tutmazsa global ağırlık ölçeğini ayarlayacağız. Bu ayar yalnızca "beyin canlı ama epileptik değil" koşulu için yapılacak.

### Z-02 · Görme sinyali merkezi beyne ulaşabilecek mi? 🟢

Fotoreseptörlerden inen nöronlara kadar birçok sinaptik katman var. Eşit ağırlık varsayımıyla sinyal bu katmanlarda sönebilir ya da kontrolden çıkabilir.

**Faz 1 bulgusu (2026-09-16):** Sorun beklenenden temel çıktı. Fotoreseptörler **histaminerjik**, yani ilk sinapsları ketleyici. Fotoreseptörlerden motor havuzlarına **hiç uyarıcı yol yok**. Shiu modelinde nöronlar uyarı yokken sessiz. Sessiz bir nöronu ketlemek hiçbir şey değiştirmediği için fotoreseptörleri doğrudan uyarmak **hiçbir aşağı akış aktivitesi üretmez**.

Gerçek sinekte böyle olmuyor: lamina nöronları ışıkta sürekli aktif ve ışık değişimleri bu aktiviteyi aşağı ya da yukarı kaydırıyor. Sinek gözü aslında büyük ölçüde **kontrast** algılıyor. Aynı sorun sonraki katmanlarda da tekrar ediyor (L1 glutamaterjik, dolayısıyla modelde ketleyici).

**Çözüm seçenekleri (Faz 3'te deneyle seçilecek):**
- **(a) Tonik taban aktivite:** Görme sistemine sürekli bir arka plan uyarımı verilir, görsel bu tabanın etrafında dalgalanma yaratır. Biyolojiye en yakın seçenek bu, fakat yeni bir parametre ekliyor (taban hızı).
- **(b) Kolon nöronlarından giriş:** İşaret dönüşümü elle uygulanır ve görsel, kolon koordinatı olan nöronlara (L2 uyarıcı; Mi1, Tm1...) verilir. Karanlık bölgeler L2'yi daha çok ateşler. Basit bir yöntem, ancak fotoreseptör katmanı atlanmış olur.
- **(c) İkisinin birleşimi.**

Her durumda kalibrasyon katman katman aktivite ölçümüyle yapılacak (fotoreseptör → lamina/medulla → lobula → merkezi beyin → inen nöronlar).

**Faz 3 çözümü (K-012):** Üç yöntem denendi. Sonuçlar:
- Tonik aktivite (a, "foto" yöntemi) başarısız: gri ekranda bile yaklaşık 15 bin nöronu sürekli ateşletiyor ve sinyali merkeze ulaştıramıyor.
- Yalnızca OFF girişi (b'nin yarısı) optik lobda kalıyor.
- **ON ve OFF birlikte** (karanlık → L2/L3, aydınlık → Mi1/Tm3, 250 Hz) sinyali görme projeksiyon nöronlarına, merkezi beyne, inen nöronlara ve motor nöronlara taşıyor. 16 doğal istatistikli görseli %95–100 ayırt ediyor.

Bir koşul gerekti: kodlayıcının sürdüğü nöronların sinaptik depresyondan muaf tutulması. Ayrıntılar: [07-duyular.md](07-duyular.md).

### Z-03 · Plastisite yok, dolayısıyla öğrenme de yok 🔴

LIF modelinde bağlantılar sabit. Sinek beğeni alsa bile bundan bir şey öğrenmez. Böyle kalırsa feed yalnızca Instagram'ın algoritması tarafından şekillenir.

**Çözüm yolu (Faz 10):** Mantar gövdesinde (mushroom body) dopaminle kapılanan bir öğrenme kuralı eklemek. Sinekteki öğrenmenin gerçek mekanizması bu: Kenyon hücresi → MBON sinapsları, dopamin sinyali geldiğinde zayıflar. Ödül (beğeni, takipçi) PAM nöronlarını uyarır; böylece sinek neyin ödül getirdiğini öğrenebilir.

### Z-04 · Sinek resim yemez: "beğen" hiç tetiklenmeyebilir 🟢

MN9 (hortum uzatma) gerçek sinekte asıl olarak **tat** ile tetiklenir, görüntüyle değil. Biyolojik olarak doğru bir model gördüğü görsele hortum uzatmayabilir.

**Çözüm yolları:** (a) Bunu kabul etmek: sinek nadiren beğenir ve bu durum da bir sonuçtur. (b) Kokunun (caption) beslenme devrelerini etkilemesine izin vermek. (c) "Beğen" eylemini bir yaklaşma davranışına bağlamak (hedefe dönme + ileri yürüme). Karar Faz 4'te, gerçek aktivite verisine bakılarak verilecek.

**Faz 4:** Beklenen olmadı; hortum motor nöronları görsel + caption postlarında düşük hızda ama tutarlı biçimde ateşliyor (67 hortum MN'si, tutarlılık r = 0,93). Beğen ve kaydet bu kanaldan, iki şiddet eşiğiyle okunuyor (K-018).

### Z-05 · Sinek okuyamaz 🟢

Caption'lar metin; sineğin dil diye bir yetisi yok.

**Çözüm yolu:** Kelimeleri kokuya çeviriyoruz (bkz. [mimari](02-mimari.md)). Bu eşleme keyfi fakat **sabit**. Sinek anlamı değil, kokuyu ayırt eder. Anlamlı bir metin beklemek gerçekçi değil; ortaya çıkacak şey sineğin "koku zevkini" yansıtan bir kelime dizisi.

**Faz 3:** Kodlayıcı yazıldı (K-013). Görselle birlikte verildiğinde 4 farklı caption %52 doğrulukla ayırt ediliyor (şans %25). Görsel sinyali baskın, ama caption'ın etkisi ölçülebilir düzeyde.

### Z-06 · Sessiz veya epileptik beyin 🟢

Uyarı yokken model tamamen sessiz kalabilir. Çok uyarı verilirse de tüm beyin aynı anda ateşleyebilir.

**Faz 2 bulgusu (2026-09-16):** İkinci risk gerçekleşti. Orijinal Shiu ağırlıklarıyla MaleCNS, küçük bir uyarımdan sonra bile yaklaşık 12–13 bin nöronun **uyarım bittikten sonra da** ateşlemeye devam ettiği kalıcı bir çekiciye kilitleniyor. Çekicinin merkezi koku lobundaki güçlü karşılıklı uyarıcı döngüler. Girdiden bağımsız olduğu için bu durumdaki beyin, farklı postları birbirinden ayırt edemiyor. Ayrıntılar ve ölçümler: [06-simulasyon.md](06-simulasyon.md).

**Denenenler:**
- Global ağırlık ölçeği: 0,5 civarında tat uyarımları için kararlı hale geliyor, ama koku uyarımları 0,4'te bile kilitleniyor.
- Sinaptik depresyon ve ateşleme hızı adaptasyonu: kilitlenmeyi söndürüyor, ancak şeker→MN9 sinyalini de zayıflatıyor.

**Çözüm (K-011):** Ağırlık ölçeği 0,70 ile duyu nöronlarını muaf tutan kısa süreli sinaptik depresyon (U = 0,2, τ = 800 ms) birlikte kullanılıyor. Bu ayarda 96 koku ve 12 tat denemesinin hiçbirinde kalıcı aktivite kalmadı. Bedeli, orijinal ayara göre daha zayıf bir şeker→MN9 yanıtı (3,7 Hz, seçiciliği korunuyor). Kalibrasyon protokolü (nötr uyaranda taban hızlar → eşikler) Faz 4'te uygulanacak.

**Hâlâ izlenecek:** Bu ayar görsel girdilerle henüz denenmedi. Görsel girdiler çok daha fazla nöronu aynı anda uyaracak; Faz 3'te kararlılık yeniden ölçülecek.

---

## Mühendislik zorlukları

### Z-07 · Hesaplama maliyeti 🟢

166.000 nöron, 0,1 ms adım: 1 saniyelik simülasyon 10.000 adım ediyor. Benzer bir NumPy uygulaması (FlyWire, 139 bin nöron) dizüstü bilgisayarda simülasyonun 1 saniyesi başına yaklaşık 8 saniye harcıyor.

**Çözüm yolları:**
- **Olay güdümlü güncelleme:** Her adımda nöronların yalnızca küçük bir kısmı ateşliyor. Bu yüzden seyrek matrisin yalnızca ateşleyen sütunlarını toplamak yeterli.
- Numba ile derlenmiş çekirdek; Apple Silicon üzerinde PyTorch/MPS seçeneği de denenecek.
- **Zaman ayrıştırma:** Instagram gerçek zamanlı yanıt beklemiyor. Beyin hesap yaparken tarayıcı postta bekleyebilir. Bakma süresini duvar saati değil, simülasyon zamanı belirler.

**Faz 2 ölçümü:** Olay güdümlü Numba çekirdeği tek çekirdekte simülasyonun 1 saniyesini yaklaşık 1,2 saniyede hesaplıyor; ağır aktivitede bile 1,3 saniyeyi geçmiyor. Bu, 500 ms'lik bir karar penceresi için yaklaşık 0,6 saniye demek. Paralelleştirmeye şimdilik gerek yok. Deney taramaları 5 işlemle paralel çalıştırılıyor.

### Z-08 · Bellek ve disk 🟢

Makine: 16 GB RAM, yaklaşık 35 GB boş disk. Bağlantı tablosu 1 GB (feather); bellekte 3,5 GB'a çıkıyor (152 milyon satır).

**Çözüm:** Yalnızca gereken üç dosya indirildi (1,1 GB). 12,7 GB'lık sinaps noktaları dosyası indirilmedi. Tablo memory-map ile açılıp pyarrow ile süzülüyor. Önbellek üretimi 3 saniye sürüyor, bellek kullanımı en fazla 4,4 GB'a çıkıyor ve sonuç diskte 54 MB tutuyor.

### Z-09 · Görsel → ommatidyum eşlemesi 🟢

Bir görseli doğru fotoreseptöre vermek için her fotoreseptörün hangi göz kolonunda olduğunu bilmek gerekiyor.

**Faz 1 bulgusu:** Anotasyon tablosunda 15 kolon nöron tipi için kolon koordinatı (`hex1`, `hex2`) var; göz başına yaklaşık 890 kolon. **Fotoreseptörlerde bu bilgi yok.** Sol gözde R1–R6'nın yalnızca 501'i var (sağda 893); sol göz eksik.

**Çözüm yolu:** Her fotoreseptörün kolonu, en çok sinaps yaptığı kolon nöronunun (R1–R6 için L1/L2/L3, R7/R8 için Mi1/Tm...) koordinatından çıkarılacak.

**Ön deneme (2026-09-16):** Koordinatlı çıkış partnerlerinin sinaps ağırlıklı oylamasıyla yapıldı.

| Tip | Kolon atanan | Oy payı (medyan) | Not |
|---|---|---|---|
| R1–R6 | %99 (1.382 / 1.394) | 1,00 | Başlıca partnerler L2 ve L1; atamalar belirsizlik içermiyor |
| R8 | %96 (1.271 / 1.329) | 1,00 | |
| R7 | %46 (593 / 1.299) | 1,00 | Çıkışlarının çoğu kolon koordinatı olmayan Dm8 nöronlarına gidiyor; eksikler aynı ommatidyumdaki R8 eşi üzerinden tamamlanacak |

Atanan her fotoreseptör, bağlandığı kolon nöronuyla aynı tarafta. Sol göz eksikliği görselin sol yarısını daha zayıf "görmek" anlamına geliyor. Bu biyolojik değil, veri kaynaklı bir asimetri; Faz 3'te telafi edilip edilmeyeceğine karar verilecek.

**Faz 3 çözümü:**
- İkinci tur oylamayla R7 kapsamı %99'a çıktı.
- Kolon ızgarasının geometrisi ve bakış yönleri lamina hücre gövdelerinden çıkarıldı; gözün üst kenarı doğru yönde çıkıyor.
- Kullanılan giriş nöronları (L2, L3, Mi1, Tm3) iki gözde de hemen hemen eksiksiz; sol göz eksikliği yalnızca fotoreseptörleri etkiliyor ve seçilen yöntem (K-012) fotoreseptörleri kullanmıyor.

Ayrıntılar: [07-duyular.md](07-duyular.md#göz-geometrisi).

### Z-16 · Ağ çok sıkı bağlı: özgüllük nereden gelecek? 🔴

Her duyu, beynin yaklaşık %98'ine birkaç sinaptik adımda ulaşıyor. Şeker nöronları da, acı nöronları da, dopamin nöronları da her motor havuzuna 2–3 adımda erişebiliyor.

**Anlamı:** Hangi davranışın ortaya çıkacağını topoloji değil, sinaps sayıları ve işaretler belirleyecek. Uyarım çok güçlü olursa her şey ateşler ve davranış ayırt edilemez hale gelir.

**Çözüm yolu:** Faz 2'de uyarım yoğunluğuna karşı yanıt eğrileri çıkarılacak. Seçicilik ölçütü şöyle olacak: şeker MN9'u ateşletmeli, acı ateşletmemeli.

### Z-17 · Modülatör nörotransmitterlerin işareti belirsiz 🟡

Dopamin, serotonin ve oktopamin reseptöre göre uyarıcı da olabilir ketleyici de. Model tek bir işaret istiyor.

**Geçici çözüm:** Hepsi uyarıcı kabul edildi (K-008). Bu nöronlar toplamın %0,3'ü. Faz 10'da dopamin, öğrenme kuralındaki rolüyle (işaret yerine plastisite sinyali olarak) ayrıca modellenecek.

### Z-18 · Sabit görseller dönme davranışını tetiklemiyor 🟡

Solda ya da sağda duran koyu bir daire, dönme komut nöronlarında (DNa02) belirgin bir sol-sağ farkı yaratmadı (en fazla 1 Hz). Gerçek sinekte de dönme büyük ölçüde hareketle tetikleniyor.

**Anlamı:** "Sekme değiştir = dönme" eşlemesi sabit görsellerle nadiren tetiklenebilir.

**Çözüm yolları (Faz 4):** (a) Bunu kabul etmek. (b) Görseli küçük göz hareketleri (sakkadlar) ya da feed kaydırma hareketiyle sunmak; bu, T4/T5 hareket devrelerini de devreye sokar. (c) Reels videolarının kendi hareketinden yararlanmak.

**Faz 4:** Dönme artık DNa02 yerine boyun motor nöronlarının sol−sağ farkından okunuyor. Bu fark her postta var ama tekrarlar arasında tutarlılığı düşük (r ≈ 0,2–0,3). "Sekme değiştir" eyleminin yönü bu yüzden büyük ölçüde gürültüye dayanıyor. Hareket girdisi (b, c) Faz 7'de zamansal görmeyle birlikte ele alınacak (Z-25).

### Z-19 · Komut nöronları sessiz 🟢

Literatürde davranış başlatan tekil komut nöronları (ileri yürüme için DNp09/oDN1, kur yapma için P1, yutma için MN11/12, tımar için aDN) gerçekçi postlarda hiç ateşlemedi.

**Çözüm (K-015):** Okuma, vücut bölgesine göre gruplanmış kas kanallarından yapılıyor. Takip et (K-017) ve kaydet (K-018) bu kanallara taşındı.

### Z-20 · Motor yanıtı başlangıçta toplanıyor, sonrası seyrek 🟢

Kas aktivitesinin neredeyse tamamı postun ilk 500 ms'inde. Sonraki pencerelerde kaçış kanalı dışında kanallar neredeyse sessiz; bu, sinaptik yorulmanın beklenen sonucu. Sessiz pencerelerde standart sapma çok küçük olduğu için tek bir spike z ≈ 30 üretip, örneğin "kaydet" kararını tetikleyebiliyordu.

**Çözüm:** Standart sapmaya sayma gürültüsü tabanı uygulanıyor. Tek bir spike en fazla yaklaşık 1 standart sapmalık kanıt sayılıyor.

### Z-21 · Simülasyon hızı: görsel girdi pahalı 🟢 (hedefte; sınırda)

Görsel girdide yaklaşık 7.400 nöron her 0,1 ms'de rastgele sayı çekiyor. Buna 165 bin nöronluk durum güncellemesi de eklenince bir postun 1,8 saniyelik simülasyonu tek çekirdekte birkaç saniye sürüyor.

**Çözüm yolları:**
- Poisson olaylarını olay zamanlamasıyla üretmek (rastgele sayı sayısı yaklaşık 40 kat azalır, ama rastgele sayı akışı değişir ve önceki deney sonuçları birebir tekrarlanamaz).
- Durum güncellemesini Numba ile paralelleştirmek.

3D gövdeyle birlikte önemi arttı: beyin, fizik ve görme aynı döngüde çalışacak. Fizik tek başına gerçek zamandan hızlı (tüm eklemlerle 1,3 kat), yani darboğaz beyin. Faz 5 hedefi: kapalı döngü gerçek zamanın en fazla 3 katı yavaşlıkta.

**Durum (2026-09-17):** Beyin, gövde, görme ve telefon ekranı birlikte tek süreçte gerçek zamanın ~4–5 katı yavaş çalışıyor. Hedefin (3 kat) hâlâ gerisinde.

**Durum (2026-09-17, hızlandırma):** Kapalı döngü artık gerçek zamanın **2,95–3,25 katı** yavaşlıkta çalışıyor (4 iş parçacığı). Tek iş parçacığında 3,9–4,1 kat.
- **Profil (önce, 1 sn simülasyon, 4,5 sn):** beyin 2,2 sn, fizik 1,0 sn, görme 1,2 sn (çizim ve piksel okuma 0,64, kolon örneklemesi ~0,55).
- **Beyin:** Paralel ve dallanmasız güncelleme; 2,2 sn'den 1,1 sn'ye ([06-simulasyon.md](06-simulasyon.md#performans)). Sonuç bit düzeyinde aynı.
- **Görme:** Kolon örneklemesi tek bir Numba döngüsüne alındı (grup, kanal ve göz başına 24 ayrı interpolasyon yerine). Kare başına 4,7 ms'den 0,5 ms'ye indi. Sonuç 10⁻¹⁴ düzeyinde aynı; uyarılan nöronlar ve hızları (10⁻¹¹ Hz) değişmedi.
- **Uçtan uca kontrol:** Eski ve yeni kodla aynı 9 gövdeli deneme (yaklaşma, solma, kaydırma) birebir aynı dev lif, LC4 ve sıçrama sonucunu verdi.
- **Kalan (1 sn başına):**
  - fizik 1,1 sn (0,1 ms'lik 10 alt adım; enerji hesabını kapatmak fark etmedi),
  - beyin 1,1 sn,
  - göz çizimi ve piksel okuma 0,6 sn,
  - solma sırasında ekran karışımı ~0,1 sn.
- **Sonuç değiştireceği için yapılmayanlar:** Poisson çekilişlerini seyreltmek, göz kamerası çözünürlüğünü düşürmek, fizik zaman adımını büyütmek.
- **Deneylerin süreç havuzları:** Her işçi 1 iş parçacığı kullanıyor; kazanç yalnızca görme örneklemesinden ve dallanmasız güncellemeden geliyor.

---

## Gövde ve görselleştirme zorlukları

### Z-22 · Sinaptik depresyon sürekli komutları boğuyor 🔴

K-011'deki depresyon (U = 0,2, τ = 800 ms), ateşleme hızı ne kadar yüksek olursa olsun bir sinapsın iletimini saniyede en fazla 6,25 tam spike'a eşdeğer düzeyde tutuyor. Faz 2'de kalıcı çekiciyi önleyen bu mekanizma, yürüme komut nöronu DNg100 saniyede 180 kez ateşlediğinde bile ritim çekirdeğini tamamen sessiz bırakıyor. İnen nöronlar muaf tutulunca çekirdek ve 30–70 bacak motor nöronu ateşliyor ([09-govde.md](09-govde.md#3-yürüme-ritmi-yoklaması-dng100)).

Aynı sorun kaçış devresinde de çıktı: dev lif 150 ms boyunca ateşlese bile TTMn'ye ulaşamadı. Orada asıl eksik elektriksel sinapstı (K-023).

**Çözüm yolları:**
- İnen nöronları (ya da sinir kordonunu) depresyondan muaf tutmak. Muafiyetin kalıcı çekiciyi yeniden getirip getirmediği kararlılık testleriyle ölçülmeli.
- Depresyonu hücre tipine göre ayarlamak (ör. inen nöron sinapslarında daha kısa τ). Parametreler ancak literatürdeki ölçümlere dayanıyorsa kullanılabilir.

### Z-23 · Bacaklar arası koordinasyon ve gövdeden gelen his 🔴

Pugliese ve ark. (2025), konnektomun tek bir bacakta ritim ürettiğini, ama bacaklar arası koordinasyonun (tripod yürüyüş) gövdeden gelen his olmadan ortaya çıkmadığını bildiriyor. Bizim ölçümümüzde ritim zayıf; tepe frekansın güç payı 0,06–0,10.

**Çözüm yolları:**
- Propriyosepsiyon: eklem açısı, yük ve zemin teması → konnektomdaki karşılık gelen duyu nöronları.
- Ritmi kas grubu başına ölçmek. Bükücü ve açıcı kaslar zıt fazda çalıştığından toplam ölçüm ritmi gizliyor olabilir.
- Pugliese ve ark.'nın kullandığı nöron boyutuna göre uyarılabilirlik ölçeklemesini değerlendirmek.
- **Yapılmayacak:** Hazır ritim üreteci eklemek (K-019).

**Durum (2026-09-17):**
- **Propriyosepsiyon eklendi (K-024):** Uyluk kordotonal organı ve kıl plakaları, 389 nöron.
- **Sonuç:** DNg100 altında bacak motor nöronu spike'ları biraz arttı (1.112 → 1.578), ama koordinasyon çıkmadı. Önündeki engel sinir kordonunun kazancı (Z-31).

### Z-24 · Kas–eklem eşlemesi ve kuvvet ölçeği 🟡

Motor nöronlar kas adıyla etiketli, ama NeuroMechFly'ın eklem serbestlik derecelerine hangi kasın hangi yönde tork uyguladığı bir tablo olarak hazır değil. FlyGym'deki kas modeli yalnızca sol ön bacakta var ve deneysel.

**Çözüm yolu:** Anatomi literatüründen (bacak kaslarının bağlanma noktaları ve işlevleri) bir tablo derlemek, kaynaklarını belgelemek. Kuvvet ölçeğini kas fizyolojisinden ve eklem sertliğinden türetmek. Davranışa bakıp ayarlama yapılmayacak.

**Durum (2026-09-17):** 105 kas, 701 motor nöron eşlendi (K-019 eki).
- **Bacaklar:** Moment kolları ve kuvvetler FlyGym'deki kas-iskelet modelinden geliyor. Orta ve arka bacaklar ön bacağın geometrisiyle, yapısal benzerlik varsayımıyla eşlendi.
- **Diğer bölgeler:** Tork ölçeği varsayıma dayanıyor.
- **Eşlenmeyen:** Femur döndürücü, halter, anten ve retina kasları.

### Z-25 · Korku tepkisi zamansal görme gerektiriyor 🔴

Kaçış devresi (LPLC2/LC4 → dev lif DNp01 → TTMn) konnektomda mevcut. Ama bu devre yaklaşan (büyüyen) nesnelere tepki veriyor. Durağan bir post görseli bu tepkiyi üretemez.

**Çözüm yolları:**
- Görme kodlayıcısına zaman boyutu eklemek: Reels videoları kare kare, kaydırma hareketi ekranda gerçek hareket olarak.
- Kaynak testi: yaklaşan bir disk dev lifi ateşletiyor mu? Hareket yönünü seçen T4/T5 devrelerinin LIF modelinde çalışıp çalışmadığı bilinmiyor.

**Durum (2026-09-17):**
- **Zamansal kodlama eklendi (K-027):** Gövdeli sinekte her kolon parlaklığa uyum sağlıyor; L2, Mi1 ve Tm3 geçici yanıt veriyor.
- **Tetikleme sorunu çözüldü:** Durağan sahne artık dev lifi ateşletmiyor. Durağan kodlamada ateşletiyordu (63 Hz).
- **Açık:** Yaklaşan nesne testi, sahne kurulduktan sonra yapılacak.

**Durum (2026-09-17, sahne):**
- **Yaklaşan disk kaçışı tetikliyor:** Telefon ekranında büyüyen koyu disk (l/v 40 ms) 125 Hz'de denemelerin %91'inde (20/22) dev lifi ateşletiyor. Sinek sıçrıyor; LC4 yüzlerce spike üretiyor ([09-govde.md](09-govde.md#12-yaklaşan-nesne-ve-görme-kazancı-2026-09-17)). Uçtan uca zincir çalışıyor: ekran → göz kameraları → kolonlar → LC4 → dev lif → TTMn → orta bacaklar.
- **Açık:**
  - İlk dev lif spike'ı disk en büyük boyuna ulaştıktan sonra, çarpışma anının +7 ile +40 ms sonrasında geliyor (medyan).
  - Gerçek sineklerde kalkışın zamanı l/v'ye bağlı; literatürle nicel karşılaştırma yapılmadı.
  - von Reyn ve ark. (2014) dev lifin kısa, uçuş dengesini feda eden kalkışı zorladığını gösteriyor. Bizim sineğimizde yalnızca bu yol var: uzun kalkış dizisi ve uçuş yok (Z-26).

**Durum (2026-09-17, özgüllük kontrolleri):** Kaçış devresi yaklaşmaya özgü değil.
- **Ölçüm** (125 Hz, açık tema, 8'er deneme; `python -m flybrain.experiments.escape --rmax 125 --kontroller --dopamin`):

  | Uyaran | Dev lifin ateşlendiği deneme | Ort. dev lif spike'ı | Ort. LC4 spike'ı | Sıçrama |
  |---|---|---|---|---|
  | Yaklaşan disk | 8/8 | 17,5 | 178 | 8 |
  | Kararma: diskin son bölgesi büyümeden, aynı zamanlama ve aynı toplam kararmayla | 7/8 | 14,0 | 136 | 7 |
  | Kaydırma | 8/8 | 9,4 | 96 | 7 |
  | Yalnızca post görseli kayıyor (geniş alan hareketi) | 1/8 | 0,5 | 7 | 1 |
  | Durağan | 2/8 | 0,2 | 3 | 1 |

- **Tekrar:** İlk yoklamada (500 ms bekleme, farklı postlar) kararma yaklaşmadan da güçlüydü: 8/8 ve 22,9 spike'a karşı 7/8 ve 14,0.
- **Gerçek sinekle fark:** Yaklaşma algılayıcısı LPLC2 kenarların dışa doğru yayılmasına seçici. Kararmaya, daralmaya ve geniş alan kaymasına yanıt vermiyor (Klapoetke ve ark. 2017). Modelde kararma, yaklaşma kadar güçlü kaçış tetikliyor.
- **Kaydırmadaki kaçışın kaynağı:** Görselin kayması tek başına zayıf. Kaçışı, ekrandan geçen geniş açık-koyu alanlar tetikliyor (Z-35).
- **Olası neden (ölçülmedi):** Hareket yönünü T4/T5 hücreleri, hızlı ve yavaş girdilerin zaman farkıyla hesaplıyor. Örneğin T5'e giden Tm9 alçak geçiren, Tm1, Tm2 ve Tm4 bant geçiren süzgeç gibi davranıyor (Arenz ve ark. 2017).
  - Bizim LIF modelde bütün nöronların zaman sabitleri aynı.
  - Görme yalnızca L2, L3, Mi1 ve Tm3'e veriliyor.
  - Bu yüzden yön seçiciliği büyük olasılıkla oluşmuyor.
- **Çözüm yolu:**
  1. Kayan çizgilerle T4/T5'in yön seçiciliğini ölçmek.
  2. Girdi hücrelerine ölçülmüş zamansal süzgeçleri vermek.
  3. Kontrollerle doğrulamak: yaklaşma kaçışa yol açmalı; kararma, uzaklaşma ve kayma nadiren.
- **Koyu tema (K-030):** Yaklaşan diske kaçışı %96'dan %77'ye indiriyor; kararma ise koyu temada da güçlü kalıyor (8 denemede yaklaşma 5, kararma 6).
- **Şimdilik:** Kullanıcı yalnızca ekran tarafını seçti (K-030). Korku tepkisinin anlam taşıması gereken Faz 7'de bu sorun yeniden ele alınmalı: sinek her karanlık görselden de kaçabilir.

### Z-26 · Uçuş yok 🟡

Uçabilen hazır gövde modelinin (flybody) uçuş kontrolcüsü eğitilmiş bir sinir ağı; kullanılamaz. Uçuş aerodinamiği ve dolaylı uçuş kaslarının mekaniği ayrı bir iş.

**İlk sürüm:** Kaçış sıçrama olarak görünür (TTMn → orta bacaklar), sinek uçmaz. Kur şarkısı için kanat titreşimi ayrıca modellenecek.

**Gözlem (2026-09-17):**
- **Sıçrama çalışıyor:** 1,2 mm yükselme, 3,3 mm sıçrama.
- **Denge riski:** Sinek yere oturmamışken tetiklenirse havada takla atıp sırtüstü düşüyor. Gerçek sinek bu durumda kanatlarıyla toparlanır. Bizim sineğimiz toparlanamıyor, sırtüstü de doğrulamıyor (Z-29).

**Durum (2026-09-17, uzun oturum):**
- **Sonuç:** Oturmuş sinek de kaçış sıçramasından sonra çoğu zaman sırtüstü iniyor ve öyle kalıyor. 80 postluk oturumlarda 6 sinekten 5'i düştü; pencerelerin %60'ında sinek dik değildi.
- **Karar (kullanıcı, K-031):** Deneyci sineği 1 sn sonra yeniden yerleştiriyor ve 1 sn tutuyor. Doğrulma davranışı açık bir iş olarak kalıyor.
- **Yan yatma (K-031 güncellemesi):** Sinek tam devrilmeden ~55° yatık, kararlı bir duruşa da takılıyor (göğüs alçakta, bacaklar dağınık, bir dakikaya kadar). Bu sırada bacaklar dik duruştakinden çok hareket ediyor. Yerleştirme eşiği 0,5'ten 0,9'a çıkarıldı (09-govde.md 17.7).

### Z-27 · Nöral karar ile görünen hareketin tutarlılığı 🟡

Instagram eylemleri nöral okumadan seçiliyor, gövde aynı nöronlarla hareket ediyor (K-020). Yine de iki tutarsızlık olasılığı var:
- **İlgi kaybı:** Hiçbir kanal eşiği aşmadığında feed kayıyor, ama gövdede buna karşılık gelen bir hareket yok.
- **İleri kanalı:** Bacak motor nöronlarının toplamını okuyor. Sinek yürümeden (ör. yerinde kıpırdanarak) bu eşiği aşabilir.

- **Faz 4 okumasında bir hata:** TTMn ve STTMm (sıçrama kasları), kanat alt sınıfında oldukları için "yorum" kanalında sayılıyor. Oysa gövdede sıçrama üretiyorlar; "çıkış" kanalına taşınmalılar (yeniden kalibrasyon gerekir).

**Çözüm yolu:** Her kararda ilgili gövde bölgesinin hareketini ölçüp raporlamak. Örtüşmeyen durumlar veriye bakılarak kullanıcıyla birlikte çözülecek.

- **Propriyosepsiyonla yeni bir gözlem (2026-09-17):** Bir DNg100 koşusunda TTMn 3 kez ateşledi ve sinek yürüme komutu altında sıçramaya benzer bir hareket yaptı.
  - **Yol:** Propriyoseptörler, uyarıcı ara nöronlar (IN20A.22A001, GFC2) üzerinden TTMn'ye ulaşıyor.
  - **Tekrarlanma:** Aynı koşulun başka koşularında görülmedi.

**Durum (2026-09-17, gövdeli kararlar, K-032):**
- **Ölçüm:** Gövdeli sinekte onaysız kuralla verilen referans kararlarında ilgili bölge çoğunlukla görünür hareket etti (sonraki post %92, beğeni %96, yorum %100, tımar %88). Takip (%38), çıkış (%44), sekme (%0) ve önceki post (%0) örtüşmedi (tablo: 09-govde.md 17.4).
- **Karar (kullanıcı, K-032):** Gövde onayı şartı. Bir kanal ancak o pencerede kendi bölgesi görünür hareket ettiyse karar verebiliyor. Sıçramalı pencerede yalnızca çıkış onaylanıyor.
- **Yapıldı:** TTMn ve STTMm yorum kanalından çıkarıldı. Gövdesiz sineğin kalibrasyonu yenilendi.
- **Açık:**
  - İlgi kaybında akış yine hareketsiz kayıyor.
  - Onay, bölgenin hareket ettiğini gösteriyor; hareketin kararı veren nöronlardan geldiğini göstermiyor.
  - Onaylı kuralda sekme ve önceki post neredeyse hiç seçilmiyor: baş eklemleri ve geri yürüme nadiren görünür hareket ediyor.
  - Uzun oturumda sonraki post ile ilgi kaybı sineğin etkinlik dönemleriyle salınıyor. Durgun sinek bacağını oynatmayınca sonraki post onaylanmıyor; homeostaz bunu düzeltemez (09-govde.md 17.9).

### Z-28 · Görselleştirme verisinin boyutu ve canlı izleme 🟡

- **Veri hacmi:** 165 bin nöronun spike'ları, 126 eklemin açıları ve ekran kareleri, saniyede yüzbinlerce olay demek.
- **Hız:** Simülasyon gerçek zamandan yavaş.

**Çözüm yolları:**
- Sıkıştırılmış oturum kaydı ve gerçek hızda oynatma.
- Canlı modun ağır çekim olarak açıkça etiketlenmesi.
- Beyin görünümünde spike'ların kısa zaman kutularında toplanması.

**Durum (2026-09-17, K-033):**
- **Kayıt:** 44 sn'lik bir oturum 30 MB tutuyor: 6,8 milyon spike 11 MB'a sıkışıyor, videolar 14 MB. Kayıt simülasyonu ~4 kat yavaşlatıyor.
- **Oynatma:** Panel ve video kayıttan gerçek hızda ya da etiketli ağır çekimde oynatıyor. Beyin görünümünde her spike üstel sönümle (60 ms) parlıyor.
- **Açık:**
  - Canlı mod yok.
  - Panel spike dizisini tek parça yüklüyor (44 sn için 27 MB). Uzun oturumlarda parçalı yükleme gerekecek.

### Z-29 · Duruş tonusu yok 🔴

Gerçek sinekte yavaş motor nöronlar dururken de tonik ateşleyerek duruşu korur. Bizim modelde dinlenen beyin tamamen sessiz. Kas modelinin pasif sertliğiyle sinek çömeliyor (göğüs 0,68 mm); sıçramadan sonra sırtüstü kalırsa doğrulamıyor.

**Çözüm yolları:**
- Gövdeden gelen his: yük ve eklem açısı refleksleri tonik aktivite üretebilir.
- Sinir sistemindeki kendiliğinden aktivite: biyolojik gürültü (ilke 4). Kanıta dayanıyorsa eklenebilir.

**Durum (2026-09-17):**
- **Tonik girdi var:** Propriyosepsiyonla nötr pozda 31 propriyoseptör tonik ateşliyor.
- **Tonus çıkmıyor:** Motor nöronlara ulaşan saniyede 18 spike, bir tonus oluşturmuyor. Göğüs 0,64 mm'de kalıyor (Z-31).

### Z-30 · Şeker tadı tam hortum uzatma üretmiyor 🟡

Uçtan uca testte şeker tadı hortum nöronlarına ulaşıyor. Ama en çok çalışanlar arasında hortumu geri çeken MN2Da da var. Haustellum açılıyor (0,32 rad), rostrum ileri gitmiyor.

- **Karşılaştırma:** Shiu ve ark. modelinde şeker → MN9 güçlüydü.
- **Olası neden:** K-011 ayarında (düşük ağırlık, depresyon) MN9 yanıtı zaten zayıf (3,7 Hz).
- **Bağlam:** Gerçek sinekte hortum uzatma, açlık durumuna da bağlıdır; bu durum modellenmiyor.

### Z-31 · Sinir kordonunun kazancı: bacak motor nöronları yavaş 🔴

- **Ölçüm:** DNg100 uyarımı altında bacak motor nöronlarının ortalama hızı 1,6–7,8 Hz; bacak başına etkin motor nöron sayısı az. Yürümede bu nöronların onlarca Hz'e çıkması beklenir.
- **Denenenler ([09-govde.md](09-govde.md#74-yürüme-neden-çıkmıyor-sinir-kordonunun-kazancı)):**
  - Depresyonu tüm sinir kordonunda kaldırmak: 3,5 Hz.
  - Shiu ve ark.'nın orijinal sinaps ağırlığına dönmek: 7,8 Hz. Ama sıçrama kası tekrar tekrar ateşliyor, koordinasyon gelmiyor.
- **Propriyosepsiyon:** Direnç refleksi doğru yönde ama çoğu bacakta eşiğin altında kalıyor.
- **Neden (olası):** Shiu ve ark.'nın LIF modeli beyindeki duyu → karar yolları için doğrulanmıştı. Sinir kordonu için bir doğrulaması yok. Pugliese ve ark. (2025) sinir kordonunda ritmi, nöron boyutuna göre ölçeklenmiş kazanç ve eşik kullanan, 200 Hz'de doyan hız tabanlı bir modelle elde etti.

**Çözüm yolları (kullanıcıya soruldu):**
- Sinir kordonunu Pugliese ve ark.'nın hız tabanlı modeliyle simüle etmek; beyin LIF olarak kalır, arayüz inen ve çıkan nöronlar. **Seçildi (K-025); sonuç Z-33.**
- Sinir kordonu için ayrı bir kazanç, literatürdeki sinir kordonu ölçümlerine (motor nöron hızları, ritim frekansı, direnç refleksi) göre kalibre edilir (K-011'in yöntemi).
- Yürümeyi araştırma olarak paralel sürdürüp sonraki adımlara (görme, sahne, görselleştirme) geçmek.

### Z-32 · Ön bacak propriyoseptörleri ve yük algısı verisi eksik 🟡

- **Ön bacak:** MaleCNS'te ön bacakların uyluk kordotonal organı çok eksik (sol 1, sağ 0 bükülme pençesi; orta ve arka bacaklarda 12–18). ProLN'den giren 185 duyu nöronunun tipi ve modalitesi bilinmiyor.
- **Yük:** Yük algılayıcısı (kampaniform sensil) etiketi taşıyan bacak nöronu yalnızca 13.
- **Zemin teması:** Tarsal temas kıllarının hangileri olduğu etiketlerde yok.

**Çözüm yolları:**
- MaleCNS'in sonraki sürümlerini izlemek.
- FANC/BANC eşleşmelerinden tip kimliği aktarmak (indirme gerektirir).

### Z-33 · Hız modeli: ritim var ama zayıf, güçlü girdide doyum 🔴

Pugliese ve ark.'nın modeli MaleCNS'te yeniden üretildi (K-025): ön bacak ağının koşularının %98'i 11 Hz'de salınıyor. Gövdeye bağlanınca üç sorun çıktı ([09-govde.md](09-govde.md#8-sinir-kordonu-hız-modeli-2026-09-17)):

1. **İki kararlı durum:**
   - Bacak ağı ya ritim üreten düşük aktiviteli bir durumda ya da kendini sürdüren doygun bir durumda (binlerce nöron, motor nöronlar 200 Hz) duruyor.
   - DNg100'ün 15 Hz'lik spike dizisi 20 ms'lik süzgeçle anlık 90 Hz'e çıkıyor ve ağı doyuma kilitliyor. 300 ms'lik süzgeç ritmi koruyor.
   - Tüm kordon (kanat, karın, boyun ağlarıyla) DNg100 12 Hz'i geçince doyuma gidiyor. Yazarlar da 1.500'den fazla nöronun devreye girdiği koşuları "kararsız" sayıp dışarıda bırakıyor.
2. **Ritim rejiminde motor çıktı çok düşük:**
   - Etkin bacak motor nöronları 1–30 Hz'de.
   - DNg100 17 Hz'de gövde 2,8 sn'de 0,25 mm kıpırdıyor (201 motor nöron spike'ı).
   - Yazarlar da yürümede etkin olması gereken kasların çoğunun modelde sessiz ya da ritimsiz kaldığını bildiriyor.
3. **Duyu girdisinin ölçeği kalibre edilmemiş:**
   - Yazarların ağında duyu nöronları girdi almıyordu (hızları 0).
   - Bizim propriyoseptörlerimizin dinlenmedeki tonik hızları hız ağında eşiğin yüzlerce katı girdi yaratıyor ve 2.000–3.500 nöronu etkinleştiriyor.

**Çözüm yolları (kullanıcıya soruldu):**
- İki kalibrasyon: hız modeli → kas eşlemesi ve duyu girdisi kazancı. Hedefler literatürden: yürümede motor nöron hızları, dinlenmede sessiz duruş, direnç refleksinin yönü.
- Hız modeline biyolojik bir dengeleyici eklemek (ateşleme adaptasyonu). Doygun durumu sonlandırabilir; ön bacak ritminin korunduğu yeniden doğrulanmalı.
- Yürümeyi araştırma olarak bırakıp sonraki adımlara geçmek. Varsayılan model şimdilik LIF: sessiz duruş, refleksler ve sıçrama orada doğru çalışıyor.

### Z-34 · Durağan ekranda kendiliğinden kaçış: kendi hareketinden gelen görme 🟡

Sahnede sineğin dinlenirken yaptığı küçük hareketler bir döngü başlatıyor:

1. Sessiz beyinde propriyosepsiyon bacak motor nöronlarını hafifçe ateşletiyor.
2. Göğüs 200 ms'de ~0,05 mm kayıyor.
3. 2 mm uzaktaki dokulu ekranda bu kayma görme uyarımını 0'dan 170 kHz'e çıkarıyor.
4. Artan görme uyarımı bacakları daha çok oynatıyor ve sonunda dev lif ateşliyor.

**Tarama (250 Hz, 6'şar deneme, 1 sn):**

| Koşul | Kaçış |
|---|---|
| Varsayılan | 3/6 |
| Propriyosepsiyon kapalı | 0/6 (beyin tamamen sessiz) |
| Gövde sabit | 0/6 |
| Ekran kapalı (siyah) | 4/6 |
| Ekran 6 mm'de | 2/6 |

Yani döngü, ekranın içeriğinden değil, sineğin kendi hareketinden besleniyor.

**Yapılanlar:**
- Görme kazancı 125 Hz'e indirildi (K-029).
- Görme açılmadan önce 300 ms propriyosepsiyon ısınması eklendi.

**Kalan:** Durağan ekranda ~17 sn'de bir dev lif ateşlemesi (85 sn'de 5; 3'ü sıçrama).

**Çözüm yolları:**
- Duruş tonusu (Z-29) ve propriyosepsiyon kazancı (Z-33): dinlenen sinek kıpırdamamalı.
- Kendi hareketinin görmedeki izinin bastırılması. Uçan ve yürüyen sineklerde görme nöronlarına motor kaynaklı sinyaller geliyor; bu devreler konnektomda aranmalı, elle eklenemez.

### Z-35 · Kaydırma sineği kaçırıyor 🟢 (ekran tarafında; kök neden Z-25)

Ekran sineğe çok yakın (2 mm). Bu yüzden bir post boyu kaydırma, sineğin gözünde ~80°'lik ve saniyede yüzlerce derecelik bir hareket oluyor; araya giren beyaz şerit de büyük bir parlaklık değişimi yaratıyor.

**Ölçüm (125 Hz, 12'şer post çifti):**

| Geçiş | Dev lif ateşleyen deneme | Ortalama spike | Göğüs hareketi |
|---|---|---|---|
| Kaydırma, 400 ms | 12/12 | 8,8 | 2,1 mm |
| Kaydırma, 1,2 sn | 12/12 | 18,1 | 2,4 mm |
| Ani değişim | 5/12 | 1,9 | 0,4 mm |
| Solarak geçiş, 300 ms | 2/12 | 0,6 | 0,2 mm |

**Karar (kullanıcı, K-028):** Gerçek kaydırma kalıyor; sineğin kaydırmada kaçması modelin kendi öngörüsü olarak kabul edildi.

**Sonuç:** Sinek her "sonraki post" kararında sıçrayacak. Karar ile gövdenin örtüşmesi (Z-27) bu tepkiyle birlikte değerlendirilmeli.

**Durum (2026-09-17, K-030):**
- **Soru (kullanıcı):** Sinek kaçarsa akışı kaydıramaz; telefondan korkmasının önüne nasıl geçilir, telefona bakarken dopamin salgılatmak işe yarar mı?
- **Dopamin kaçışı önlemiyor:**
  - Ödül nöronları (PAM, 316 nöron), beğeni kodlayıcısının en yüksek düzeyinde (~150 Hz) bütün deneme boyunca sürüldü.
  - Kaydırmada dev lif yine 8/8 ateşledi; sıçrama 7'den 5'e, ortalama spike 9,4'ten 7,0'a indi.
  - Yaklaşan diskte 8/8'e karşı 7/8, kararmada 7/8'e karşı 8/8. Durağan ekranda dopamin tek başına kaçış üretmedi (0/8).
  - İlk yoklamada kaydırmada 8/8'e karşı 8/8 (12,0'a karşı 11,2 spike).
  - **Neden:** Modelde dopamin hızlı, uyarıcı bir verici (K-008); yavaş reseptör etkileri ve öğrenme yok. Gerçek sinekte dopaminin irkilmeye bilinen etkisi de dev lifin sıçrama refleksini kesmek değil. DopR reseptörü üzerinden, elipsoid gövdede, tekrarlanan irkilmeden sonraki uyarılmışlığı düzenliyor (Lebestky ve ark. 2009).
- **"Modelin öngörüsü" çerçevesi geri çekildi:** Kontroller kaçışın yaklaşmaya özgü olmadığını gösterdi (Z-25). Gerçek sineğin yaklaşma algılayıcısı kaydırmadaki parlaklık değişimine büyük olasılıkla yanıt vermez.
- **Ekran temaları:** Hiçbir tema kaydırmayı güvenli yapmadı (9–12/12). Solarak geçiş iki ölçümün toplamında koyu temada 2/24, açık temada 3/24 (tablo: K-030).
- **Karar (kullanıcı, K-030):** Sonraki posta solarak geçiliyor, ekran koyu temada.
- **Kalan:** Gözün seçiciliği (Z-25). Kaydırma ve anında geçiş deneyler için duruyor.

---

## Instagram zorlukları

### Z-10 · Otomasyon kullanım şartlarına aykırı 🔴

Instagram, otomatik beğeni, takip ve yorumu yasaklıyor. Hesap kısıtlanabilir ya da kapatılabilir.

**Çözüm yolları:**
- Ayrı, bu projeye özel bir hesap kullanmak.
- **Güvenlik valisi:** saatlik ve günlük eylem sınırları, eylemler arası insan benzeri bekleme süreleri. Vali eylemi yalnızca engelleyebilir, seçemez.
- Görünür (headful) tarayıcı ve kalıcı oturum kullanmak; her seferinde yeniden giriş yapmamak.
- İlk haftalarda "ısınma" dönemi: düşük eylem sınırlarıyla başlamak.
- **2026-09-19:** Isınma sınırları kaldırıldı (K-042, kullanıcı kararı). Sinek 30 postta 2-4 eylem yapıyor; sınır sineğin kararlarını engellemeye başlamıştı.

### Z-11 · Güvenlik doğrulamaları (challenge / CAPTCHA) 🔴

Instagram şüphelendiğinde doğrulama ister.

**Çözüm yolu:** Sistem bunu atlatmaya **çalışmaz**. Doğrulama algılandığında oturum durur ve kullanıcıya bildirim gider; kullanıcı doğrulamayı elle çözer, sonra sistem devam eder.

### Z-12 · Resmi API feed'i okuyamıyor 🟢

Resmi Instagram API'si yalnızca kendi hesabının içeriğini yönetmeye izin veriyor.

**Çözüm:** Playwright ile tarayıcı otomasyonu seçildi (K-006).

---

## İçerik ve etik

### Z-13 · Uygunsuz kelime kombinasyonları 🔴

Sinek, feed'den topladığı kelimelerden caption kurarken istemeden saldırgan ya da yanlış anlaşılabilecek bir dizi oluşturabilir.

**Çözüm yolu:** Güvenlik valisinde bir yasaklı kelime listesi. Liste yalnızca veto eder: yasaklı kelime seçilirse sinek bir sonraki tercihine geçer. Bu bir insan müdahalesidir ve kayıt altına alınır.

### Z-14 · Telif hakkı 🔴

Başkalarının görsellerini yeniden paylaşmak telif sorunu yaratır.

**Çözüm yolu:** Sinek başkalarının görsellerini asla yeniden paylaşmaz. Paylaşılan her görsel sineğin kendi nöral aktivitesinden üretilir. Feed görüntüleri yalnızca işlenir, saklanmaz ya da yalnızca yerel olarak küçük önizleme şeklinde tutulur.

### Z-15 · Veri lisansı 🟢

MaleCNS verisi CC-BY 4.0 lisanslı; kaynak gösterildiği sürece serbestçe kullanılabilir. Kaynak bilgisi README'de ve [kaynaklar.md](kaynaklar.md) dosyasında yer alıyor. Hesabın biyografisine de kaynak eklenmesi önerilir.

### Z-36 · Instagram arayüzü değişebilir 🟡

Eylem düğmeleri erişilebilirlik etiketinden bulunuyor (`Like`/`Beğen`, `Save`/`Kaydet`, `Follow`/`Takip et`). Instagram bu etiketleri ya da düzeni değiştirirse düğme bulunamaz.

**Şu anki durum:** Etiketler gerçek oturumda **doğrulanmadı**; yerel sahte akış sayfasında sınandı (`tests/sahte_akis.html`).

**Nasıl ele alınıyor:**
- Her eylemden sonra düğmenin durumu yeniden okunuyor. Değişmediyse eylem "başarısız" diye kaydediliyor; sessizce yanlış düğmeye basılmıyor.
- Türkçe ve İngilizce etiketler birlikte aranıyor.
- Etiket bulunamazsa eylem uygulanmıyor ve gerekçesi kayda geçiyor.

### Z-37 · Video zamanı: tarayıcı gerçek zamanda, simülasyon 3 kat yavaş 🟡

Instagram'daki videolar gerçek zamanda oynuyor; simülasyon gerçek zamanın ~3 katı yavaş ilerliyor (Z-21). Video kendi başına oynarsa sinek onu ~3 kat hızlanmış görür.

**Çözüm:** Videolar duraklatılıyor, karesi simülasyon zamanından sürülüyor (`InstaFeed.video_time`). Bedeli: ses yok ve videonun kendi kare hızındaki ince zamanlama tam korunmuyor.

**Kalan:** Video içeriğinin kaçış tetikleme oranı ölçülmedi; sert sahne kesmeleri "anında geçiş"e benziyor (K-030 tablosunda 12 denemede 1–2 kaçış).

### Z-38 · Sinek ekranda posta bakmıyordu 🟢

Kullanıcı canlı yayında fark etti: sinek posta değil, açıklamaya bakıyor gibiydi. Oturumun
**göz kaydına** (`runs/*/gozler.mp4`) bakınca dört ayrı hata çıktı — üçü, kodun doğru çalıştığını
sandığı yerlerde.

| # | Hata | Ölçülen | Çözüm |
|---|---|---|---|
| 1 | Instagram sineği akıştan çıkardı | İlk hizalı oturumun ~3 saniyesi bildirim sayfasıydı (girişin tetiklediği güvenlik uyarısı); olay kaydı o sırada post işlediğini sanıyordu | `on_feed()` / `ensure_feed()`; dönüş `akisa_donuldu` olarak kayda geçiyor |
| 2 | "Use the app" reklam bandı | y 759–794, tam genişlik; hizalanan postun alt kenarını örtüyor, sineğin gözünde parlak mavi şerit | `dismiss_app_banner()` — yalnızca web'de var, gerçek uygulamada yok |
| 3 | Hizalama okuma sırasında bozuluyor | Görsel yüklenince büyüyor, karusel yeniden boyutlanıyor; kalan sapma 672 piksele kadar | Sapma `_align`'dan dönüyor, ekran görüntüsünden hemen önce yakınsayana dek yineleniyor (≤ 8 px) |
| 4 | Aynı post oturumda üç kez | Instagram akışın **başından** `article` siliyor; indeksler iş yaparken kayıyor, okunan post bağlantısını aldığımız post olmuyor | Post indeksle değil **bağlantısıyla** adresleniyor (`_article_of`) |

**Kalan (kabul edilen):** Akışın ilk postu hizalanamıyor — görseli sayfanın üstünde kalıyor ve
sayfa zaten en üstte olduğu için aşağı itilemiyor (ölçülen sapma −348 px). Sinek onu göremeyeceği
için atlanıyor (`ALIGN_SKIP_PX = 40`, atlananlar `InstaFeed.atlanan` listesinde).

**Ders:** Ekran görüntüsü kaydı ("ekranda ne vardı") hata bulmaya yetmedi; hatayı gösteren
**göz kaydıydı** ("sinek ne gördü"). Sineğin gördüğü, kodun gösterdiğini sandığı şey değildi.

**Doğrulama:** Gerçek akışta 8 post — hepsi farklı, sapma ≤ 0,5 piksel, bant yok.

### Z-39 · Postu görmek ile kaçmak aynı büyüklüğe ters yönde bağlı 🟡

Bir uyaranın sineği kaçırması da, postun kadraja sığması da **uyaranın gözde kapladığı açıya**
bağlı — ama ters yönde. Ekran büyüdükçe kaçış güçleniyor, post kadrajdan taşıyor; küçüldükçe post
sığıyor, kaçış sönüyor.

| Ekran açısı | postun üstü gözde | LC4 | sıçrama |
|---|---|---|---|
| 180° | %11,6 | 154 | 3,24 mm |
| 90° | %25,6 | 13 | 0,04 mm |
| 70° | %37,0 | 3 | 0,04 mm |

**Nasıl ele alınıyor (K-038):** Ekran artık dünyada sabit bir nesne; mesafeyi sinek seçiyor.
Başlangıç 2,5 mm — kaçışın korunduğu en uzak nokta. Çelişki **çözülmedi**, sineğin kararına
devredildi.

**Kök neden (Z-25):** Kaçışın bu kadar büyük bir uyaran istemesi doğal değil. Gerçek sinek çok
daha küçük yaklaşmalara kaçıyor. Bizim modelde yön seçiciliği oluşmuyor (T4/T5 için gereken farklı
zaman sabitleri yok) ve görme yalnızca L2, L3, Mi1, Tm3'e veriliyor. Bu düzelirse dar ekranda da
kaçış çalışır ve sinek postu rahatça görebileceği bir mesafede durabilir.

### Z-40 · Duygu okuması tekrarlanmıyor; yorum metni bu temelde yazılamaz 🔴

K-036 yorumun metnini iki şeye dayandırıyordu: duygu sineğin nöron havuzlarından okunacak,
kelimeler o duygu içindeyken koklanarak seçilecek. Ön koşul ölçüldü (`experiments/comment.py`):
aynı kelime listesi nötr ve korku durumlarında ikişer kez koklandı.

| | 300 ms koklama | 1500 ms koklama |
|---|---|---|
| Aynı durumun iki ölçümü (gürültü tabanı) | −0,01 / 0,47 | 0,50 / 0,50 |
| Nötr ↔ korku (4 eşleşme) | 0,62 · 0,56 · −0,01 · −0,36 | 0,43 · 0,42 · 0,95 · 0,72 |

**Durum kelime seçimini değiştirmiyor.** Durumlar arası sıralama benzerliği (1500 ms'te ortalama
0,63), aynı durumun kendi tekrarlarından (0,50) daha yüksek. Etki olsaydı tersi olurdu.

**Duygu okumasının kendisi de tekrarlanmıyor.** Yaklaşan diski gördükten sonra sinek bir ölçümde
"korku", aynı koşulun öteki ölçümünde "ödül" okuyor. Havuzlar neredeyse sessiz (kalibrasyonda
korku 0,000 Hz, ödül 0,000 Hz), bu yüzden kazanan duygu sıfıra yakın farklarla değişiyor.

**Sonuç:** K-036 bu temelde uygulanamaz. K-036'nın kendi yedek planı ("fark çıkmazsa duygu
yalnızca emojiyi ve uzunluğu belirler") de geçersiz: tekrarlanmayan bir okumadan emoji seçmek,
gürültüyü duygu diye sunmak olur (ilke 3'e aykırı).

**Kök neden bulundu — havuzlar bozuk değil, dünyada uyaran yok.** Ölçüm
(`python -m flybrain.experiments.duygu --ms 2000`), nöron başına Hz:

| sonda | korku | besleme | kur | ödül | ceza | rahatsızlık |
|---|---|---|---|---|---|---|
| boş ekran | 0 | 0 | 0 | 0 | 0 | 0 |
| post | 1,66 | 0,03 | 0,02 | 0 | 0,25 | 0 |
| şeker | 0 | **0,09** | 0 | 0 | 0 | 0 |
| acı | 0 | 0,01 | 0 | 0 | **0,31** | 0 |
| **ödül (20 beğeni)** | 0 | 0 | 0 | **116,0** | 0 | 0 |
| **ceza (20 takipçi kaybı)** | 0 | 0 | 0 | 0 | **117,3** | 0 |
| doğrudan Poisson | 142,2 | 141,8 | 141,7 | 142,2 | 143,2 | 137,6 |

Her havuz doğrudan sürülünce ~140 Hz ateşliyor: tanımları ve dinamikleri sağlam. Ödül ve ceza
havuzları **kendi uyaranlarıyla 115 ve 110 Hz**'e çıkıyor, yani devreler eksiksiz çalışıyor.
Şeker beslemeyi, acı cezayı sürüyor — hepsi beklendiği gibi.

**Sessizliğin sebebi:** Sineğin dünyasında o uyaranlar hiç olmuyor. `senses/reward.py` yazılmış
ve çalışıyor ama oturum onu hiç çağırmıyor — sinek beğeni aldığını, takipçi kazandığını ya da
kaybettiğini **hiç öğrenmiyor**. Şeker de tatmıyor. Postlara bakarken korku ve ceza dışında
gerçekten hiçbir şey hissetmiyor, çünkü hissedecek bir şey verilmemiş.

**Sonuç:** "Baskın duygu" okuması sıfıra yakın hızlar arasından seçim yapıyordu; okunan şey
gürültüydü çünkü **okunacak bir şey yoktu.** Havuzları düzeltmek gerekmiyor; sineğin dünyasına
eksik girdileri bağlamak gerekiyor.

**Ama bildirimleri bağlamak da şu an yetmiyor.** Hesap okundu (salt okuma): `flybrain26`'nın
**hiç postu yok** ("Share your first photo") ve bildirim sayfasında yalnızca giriş güvenlik
uyarıları var. Beğenecek bir şey olmadığı için gelen etkileşim de yok; bildirim okuyucusu
bugün bağlansa sonsuza kadar sıfır okur.

**Bağımlılık zinciri:** yorum metni ← duygu okuması ← gerçek ödül ← gelen beğeni ← sineğin
postu olması ← **Faz 9 (içerik üretimi)**. Faz 9 bir özellik değil, duygu okumasının kilit taşı.

### Z-41 · Deneyci sineği korktuğu şeyin karşısına geri koyuyordu 🟢

Kullanıcı canlı yayında gördü: sinek bir posttan korkuyor, sonraki posta geçiyor, sonra **aynı
korktuğu posta geri dönüp yine kaçıyor**. Döngüye giriyor.

**Sebep:** Kaçıştan sonra `fly.reset()` + `fly.run(SETTLE_MS)` çalışıyordu ama ekranda **kaçtığı
post duruyordu**. Yani deneyci sineği geri getirip onu korkutan şeyin tam karşısına koyuyor ve
2 saniye öyle bırakıyordu. O sürede sinek yeniden sıçrayabiliyor (karar kaydedilmiyor) ve
sonraki posta zaten tedirgin giriyordu.

Kimsenin verdiği bir karar değildi; kimse ekranı temizlemeyi düşünmemişti.

**Çözüm:** Toparlanma sırasında ekran, o anki karenin **ortalama parlaklığında düz griye**
dönüyor (`_recovery_screen`). Parlaklık korunuyor çünkü ekran ışık yayan bir yüzey; karartmak
ya da aydınlatmak tek başına bir uyaran olurdu. Gerçek bir deneyde de hayvan geri konulurken
uyaran kaldırılır, sonra sıradaki denemeye geçilir.

**Ölçüm** (40 postluk oturumlar, gerçek akış, kuru çalıştırma):

| | Kaçış |
|---|---|
| düzeltme öncesi | 24/40 (%60) |
| 60 postluk oturum, düzeltme öncesi | 18/60 (%30) |
| **düzeltme sonrası** | **5/40 (%12,5)** |

Beş kat düşüş. Karşılaştırma tam denetimli değil (farklı postlar, farklı saat) ama mekanizma
açık ve etki büyük.

**Ders:** Hata koddaki bir satırda değil, **deney düzeneğindeydi**. Ölçüm düzgündü, kayıt
düzgündü; yanlış olan sineğe yaptığımız şeydi. Onu da ölçüm değil, **izleyen bir insan** fark
etti.

### Z-42 · Çift dokunma beğeni bırakmıyordu; test kendi varsayımını doğruluyordu 🟢

Beğeni, Instagram'ın kalp animasyonunu çıkarsın diye fotoğrafa **çift dokunarak** yapılıyor
(K-038 yanındaki kullanıcı kararı). İlk gerçek oturumda iki beğeni denemesi de doğrulamadan
geçemedi: `tıklandı ama durum değişmedi`. Hesapta beğeni kalmadı.

**Sebep:** Jest `page.mouse.dblclick` ile gönderiliyordu. Instagram telefon görünümünde
**dokunma** olaylarını dinliyor, fare çift tıklamasını değil.

**Neden test yakalamadı:** Sahte akış sayfasını (`tests/sahte_akis.html`) kendi varsayımıma göre
yazmıştım — görselde `ondblclick` vardı, fare çift tıklaması onu tetikliyordu. Test geçiyordu
çünkü **gerçeği değil, benim varsayımımı** doğruluyordu. Mock'u kendi koduna uydurmak, testi
süsten ibaret bırakıyor.

**Çözüm:**
- Jest `page.touchscreen.tap` ile iki vuruş olarak gönderiliyor (`DOUBLE_TAP_MS = 90`).
- Sahte akış artık `touchend` dinliyor, yani gerçeğin yaptığını yapıyor.
- Çift dokunma tutmazsa **kalp düğmesine** düşülüyor ve hangi yolun kullanıldığı kayda geçiyor
  ("kalp düğmesi (çift dokunma tutmadı)"). Animasyon çıkmaz ama beğeni kaydolur.

**Doğrulama:** Gerçek oturum, `@ruudnaturephotography` postunda `begen → uygulandı`, vali
günlüğünde `"uygulandi": true, "not": ""` — geri dönüş yolu kullanılmadı, çift dokunma tuttu.

**Ders:** Doğrulama katmanı (tıklamadan sonra etiketi yeniden oku) işini yaptı: hata sessizce
"başarılı" diye kaydedilmedi. Test yakalayamadı ama **gerçeğe sorduğumuz soru** yakaladı.

### Z-43 · Bağlı sinekte kaçışın gövdedeki izi göğüste değil, bacaklarda 🟢

Sinek ekrana bağlandığında (K-040) bir şey kırılıyor: "çıkış" kararı **gövde onayından**
geçmek zorunda (K-032) ve serbest sinekteki ölçüsü göğsün yükselmesi, yani sıçrama. Bağlı
sinek yükselemez. Onay hiç gelmezse sinek korksa bile karar veremez ve korku kararlardan
tamamen silinir — tam da kullanıcının istemediği şey.

**İki yanlış deneme.**

1. *Yükselme yerine savrulma.* İlk ölçüm kaçışın bağa karşı neredeyse tamamen **yatay**
   olduğunu gösterdi (20 ms'lik bağda yükselme 0,01 mm, savrulma 0,11 mm). Ölçüyü "pencere
   içinde göğsün başlangıç noktasından en büyük uzaklığı" yaptım.
2. *Bağı gevşetmek.* Savrulma eşiği (0,1 mm) ancak çok esnek bir bağla aşılabilirdi. Bağın
   zaman sabiti tarandı (10 / 20 / 40 / 80 ms) ve **beklediğimin tersi** çıktı: gevşetmek
   kaçış savrulmasını artırmıyor, yalnızca dinlenmedeki salınımı büyütüyor. 40 ve 80 ms'de
   sineğin dinlenirken savrulması kaçıştakinden **fazla**.

   | bağ | dinlenme savrulma | kaçış savrulma |
   |---|---|---|
   | 10 ms | 0,023 mm | 0,011 mm |
   | 20 ms | 0,009 mm | 0,022 mm |
   | 40 ms | 0,055 mm | 0,022 mm |
   | 80 ms | 0,016 mm | 0,009 mm |

**Doğru yer.** Gerçek sinekte dev lif (DNp01) TTM kasını sürer, o da orta bacakların trokanter
eklemini açar ve hayvan fırlar (`body/muscles.py`). Gövde gidemese de **bu hareket bacaklarda
tam olarak yapılır**. Bütün gövde ölçüleri dev lifin ateşlediği ve ateşlemediği pencerelerde
ayrı ayrı ölçüldü (`flybrain/experiments/bag.py`):

| ölçü | bağlı, dev lif > 0 | bağlı, dev lif = 0 |
|---|---|---|
| göğüs yükselme | 0,003 mm | 0,000 mm |
| göğüs savrulma | 0,005 mm | 0,001 mm |
| **TTM eklemi** | **87,2°** | **3,1°** |

**Eşik nereden geldi.** Dev lif spike'larından değil — yoksa gövde onayı kararı veren nöronu
tekrar okumuş olurdu ve K-032'nin amacı (hareketi nöronla değil gövdeyle doğrulamak) kalmazdı.
Eşik **serbest** sineğin gerçekten sıçradığı pencerelerden çıkarıldı: göğsü ≥ 0,1 mm yükselmiş
pencerelerde TTM ekleminin açı yolu. 20°: serbest sıçramaların %100'ü, serbest sakin
pencerelerin %0'ı, bağlı sakin pencerelerin %2'si.

**Yan bulgu (bedel).** Bağlı sinekte dev lif belirgin biçimde daha seyrek ateşliyor: 96
pencerede 22 yerine 4. Sebebi düzenekte değil, kopan bir geri besleme döngüsünde — serbest
sinek kaçarken **kendi hareketi** görüntüyü süpürüyor, bu LC4'ü yeniden besliyor ve kaçışı
büyütüyor. Bağlı sinekte o döngü yok. Gerçek tethered deneylerde de durum bu; korku duruyor,
daha seyrek geliyor.

**Ders:** Dünyayı değiştirince, o dünyaya bağlı **ölçütleri** de yeniden ölçmek gerekiyor.
Bağı eklemek tek satırlık bir fizik değişikliğiydi; kararın gövdeyle doğrulanması ona sessizce
bağlıydı ve ölçmeseydim korku çıktısı hiç gelmeyecekti.

### Z-44 · Sineğin beğenisi komşu posta düştü ve hiçbir yere kaydedilmedi 🟢

> **Teşhis eksikti (Z-45).** Aşağıdaki "sayfa dokunuştan önce kaydı" açıklaması asıl sebep
> değildi. Asıl sebep, eylem yolunun postu hâlâ **indeksle** bulmasıydı. Buradaki iki katman
> duruyor ama yetmedi: bir sonraki gerçek oturumda iki beğeni kararı dört başka posta düştü.

Bağlı sinekle ilk gerçek oturumda (12 post, yalnızca beğeni ve yorum açık) günlük şunu yazdı:

```
post 8/12 @vishnu___photography_: begen → begen: tıklandı ama durum değişmedi
post 9/12 @bestfeedmy:            begen → begen: zaten uygulanmış
```

Hesabın gerçek durumu okunduğunda (salt okunur denetim) tablo uyuşmadı:

| post | günlük | hesap |
|---|---|---|
| @vishnu___photography_ | uygulanmadı | beğenilmemiş ✔ |
| @bestfeedmy | "zaten uygulanmış" | **beğenilmiş** ✘ |

Vali günlüğünde (`runs/insta/eylemler.jsonl`) tek bir başarılı beğeni yok. Yani **hesapta
sineğin hiçbir yere kaydedilmemiş bir izi vardı**.

**Sebep.** Beğeni, fotoğrafa çift dokunarak yapılıyor (Z-42). Dokunulacak nokta hedef postun
en büyük görselinin merkezinden hesaplanıyordu; hesapla dokunuş arasında sayfa kaydı (Instagram
görselleri tembel yüklüyor ve düzeni yeniden boyutlandırıyor) ve dokunuş **bir sonraki postun**
fotoğrafına gitti. 9. post ona geldiğinde zaten beğenili olduğu için kod "zaten uygulanmış"
deyip hiçbir şey yapmadı — ve iz kimsenin hanesine yazılmadı.

**Neden doğrulama katmanı yakalamadı.** Tıklamadan sonra etiketi yeniden okuma (Z-42'nin
kazanımı) yalnızca **hedef postu** denetliyordu. Hedef değişmemişti, doğru; ama başka bir post
değişmişti ve oraya kimse bakmıyordu. Doğrulama "istediğim oldu mu" diye soruyordu,
"**yalnızca** istediğim mi oldu" diye değil.

**Çözüm (iki katman):**
1. `_double_tap` her vuruştan **hemen önce** `document.elementFromPoint` ile o noktada gerçekten
   hedef postun bir parçası olduğunu doğruluyor; değilse dokunmuyor ve kalp düğmesine düşülüyor.
   Tek doğrulama yetmiyordu: iki vuruş arasında da kayabiliyor.
2. Eylemden önce ve sonra **görünen bütün postların** beğeni durumu okunuyor (`like_states`).
   Hedef dışında bir post değiştiyse eylem başarısız sayılıyor ve gerekçe
   `YANLIŞ POSTA DÜŞTÜ: <bağlantı>` olarak kayda geçiyor.

**Ders.** Bir yan etkiyi yalnızca beklediğin yerde aramak, onu bulamamak demek. Z-42'de
doğrulama katmanı işini yapmıştı; burada aynı katman, kapsamı dar olduğu için sessiz kaldı.
Hesabın durumu ile günlüğün **tamamının** uyuşması gerekiyor, yalnızca hedef satırın değil.

**Hesaptaki iz ne oldu.** @bestfeedmy beğenisi geri alınmadı; olduğu gibi bırakıldı ve burada
belgelendi. Geri almak da hesaba sineğin kararı olmayan bir eylem daha yazmak olurdu. Bu yüzden
hesaptaki beğenilerden biri sineğin kararı ama **yanlış postta**: sinek @vishnu___photography_'yu
beğenmeye karar verdi, dokunuş @bestfeedmy'ye düştü.

### Z-45 · Eylemler postu hâlâ indeksle buluyordu: iki beğeni dört başka posta, yorum başka birine 🟢

Z-44'ün düzeltmesiyle 30 postluk gerçek bir oturum açıldı (bağlı sinek, beğeni ve yorum açık).
Günlük temiz görünüyordu: bir beğeni tutmadı, bir beğeni kalp düğmesiyle uygulandı, bir yorum
gönderildi, "yanlış posta düştü" uyarısı hiç çıkmadı. Hesabın salt okunur denetimi ise başka bir
tablo verdi:

| sineğin kararı | günlük | hesapta ne oldu |
|---|---|---|
| beğen @pedrophoto2020 (6) | tutmadı | beğenilmedi |
| yorum @petthee (7) | "rethimni greece" gönderildi | yorum **@kieran_dykstra2023**'e (4) yazıldı |
| beğen @swamprattler (12) | kalp düğmesiyle uygulandı | beğenilmedi |
| — | — | **@petthee (7), @icmphotoacademy, @kdenny_astro (13), @liam_alford_photography (14) beğenildi** |

Sineğin üç kararından **hiçbiri** kendi postuna gitmedi. Hesapta sineğin kararı olmayan dört
beğeni ve yanlış yerde bir yorum oluştu. @icmphotoacademy'nin postu sineğe hiç gösterilmemişti.
Yorum, sineğin üç post önce görüp geçtiği bir posta gitti; açıklamasındaki kelimeler (Rethimni,
Greece) ise yazıldığı postla değil, @petthee'nin postuyla ilgili.

**Sebep.** Z-38'de Instagram'ın akışın başından `article` sildiği ölçülmüş ve okuma, hizalama,
ekran görüntüsü postu **bağlantısıyla** bulacak şekilde düzeltilmişti. Eylem yolu unutulmuştu:
`act`, `_state`, `_icon`, `_click` ve `_comment` hâlâ `_article(self.index)` kullanıyordu. Sinek
karar verene kadar (bakış pencereleri, bağlı sinekte çırpınma nöbetleri) akışın başından post
silinmişse indeks bir sonraki posta bakıyordu. Çift dokunma o postun ekran dışındaki fotoğrafını
bulamayıp kalp düğmesine düşüyor, durum okuması ise bu arada daha da kaymış bir başka posttan
yapılıyordu. Bir karar böylece iki beğeniye dönüşebiliyordu.

**Z-44'ün katmanları neden yakalamadı.** Görünen bütün postların önce/sonra karşılaştırması
"hedef dışında değişen var mı" diye soruyordu. Ama **hedefin kendisi** de aynı kaymış indeksten
okunuyordu: değişen post hedef sanıldı ve karşılaştırmadan çıkarıldı. Z-44'te gözlenen tablo da
(8. postun beğenisi 9. postta) bu açıklamayla birebir uyuşuyor. "Sayfa dokunuştan önce kaydı"
teşhisi gözleme uyuyordu ama sınanmamıştı.

**Çözüm:**
1. Bakılan postun bağlantısı `feed.url` olarak tutuluyor. Eylemler postu `_target()` ile
   **yalnızca** bu bağlantıdan buluyor. Post sayfada yoksa indekse düşülmüyor ve hiçbir şeye
   dokunulmuyor.
2. Yorum simgesi başka bir sayfa açtıysa adresin bakılan postun kodunu taşıdığı yazmadan önce
   doğrulanıyor. Taşımıyorsa tek harf yazılmıyor.
3. Yorum gönderildikten sonra metnin sayfada göründüğü doğrulanıyor. Önceden `ok = True`
   yazıyordu, yani kod yorumun gittiğini hiç denetlemiyordu.
4. Beğeni durumu 2 saniyeye kadar bekleniyor. Geç güncellenen bir etiket "tutmadı" sanılırsa
   kalp düğmesi beğeniyi geri alırdı.
5. Yanlış posta düşme denetimi kalp düğmesinden **sonra** da yapılıyor ve hedef artık doğru.
   Düşerse eylemin hesapta bıraktığı iz sayısı (`iz`) valinin hız sınırına sayılıyor ve
   **oturum duruyor**.
6. Sahte akışa Instagram'ın silme davranışı eklendi (testte ilk `article` siliniyor). Yeni
   testler eski kodda gerçekteki hatayı birebir yapıyor, yeni kodda geçiyor.

Valinin günlüğüne bu oturumun kayda geçmeyen üç beğenisi için bir düzeltme satırı eklendi.

**Ders.** Z-38'in düzeltmesi "postu bağlantıyla bul" idi ve yalnızca sorunun görüldüğü yere
uygulandı. Aynı varsayım (indeks sabittir) kodun başka yerlerinde de yaşıyordu. Bir varsayımın
yanlış olduğu ölçüldüğünde, onu kullanan **her** yer taranmalı. İkinci ders Z-44'ten: bir
denetim, denetlediği şeyi bozuk olabilecek aynı kaynaktan okuyorsa hiçbir şey denetlemiyor.
Asıl denetim hesabın kendisiydi ve iki kez de hatayı o yakaladı.


**Hesaptaki izler ne oldu.** Dört beğeni ve @kieran_dykstra2023'teki yorum geri alınmadı; kullanıcı
Z-44'teki gibi olduğu gibi bırakılmasını ve belgelenmesini seçti.

**Doğrulama (aynı gün, 30 postluk yeni gerçek oturum).** Sinek iki beğeni ve iki yorum kararı
verdi. Hesabın salt okunur denetimi günlükle birebir uyuştu:

| sineğin kararı | hesap |
|---|---|
| beğen @fms.fossils (11) | beğenildi, çift dokunmayla |
| yorum @joeymaclennan (12): "often" | doğru postta |
| beğen @silentframesworld (16) | beğenildi, çift dokunmayla |
| yorum (29): "our young this american" | vali saatlik sınırla engelledi (K-042 öncesi) |

Öteki 28 postun hiçbiri beğenilmedi. Çift dokunma ilk kez gerçek hesapta kalp düğmesine
düşmeden tuttu: önceki "tutmadı"ların hepsi ekran dışındaki yanlış posta dokunmaktan geliyormuş.
