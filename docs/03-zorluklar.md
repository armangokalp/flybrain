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

### Z-21 · Simülasyon hızı: görsel girdi pahalı 🔴

Görsel girdide yaklaşık 7.400 nöron her 0,1 ms'de rastgele sayı çekiyor. Buna 165 bin nöronluk durum güncellemesi de eklenince bir postun 1,8 saniyelik simülasyonu tek çekirdekte birkaç saniye sürüyor.

**Çözüm yolları:**
- Poisson olaylarını olay zamanlamasıyla üretmek (rastgele sayı sayısı yaklaşık 40 kat azalır, ama rastgele sayı akışı değişir ve önceki deney sonuçları birebir tekrarlanamaz).
- Durum güncellemesini Numba ile paralelleştirmek.

3D gövdeyle birlikte önemi arttı: beyin, fizik ve görme aynı döngüde çalışacak. Fizik tek başına gerçek zamandan hızlı (tüm eklemlerle 1,3 kat), yani darboğaz beyin. Faz 5 hedefi: kapalı döngü gerçek zamanın en fazla 3 katı yavaşlıkta.

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

### Z-26 · Uçuş yok 🟡

Uçabilen hazır gövde modelinin (flybody) uçuş kontrolcüsü eğitilmiş bir sinir ağı; kullanılamaz. Uçuş aerodinamiği ve dolaylı uçuş kaslarının mekaniği ayrı bir iş.

**İlk sürüm:** Kaçış sıçrama olarak görünür (TTMn → orta bacaklar), sinek uçmaz. Kur şarkısı için kanat titreşimi ayrıca modellenecek.

**Gözlem (2026-09-17):**
- **Sıçrama çalışıyor:** 1,2 mm yükselme, 3,3 mm sıçrama.
- **Denge riski:** Sinek yere oturmamışken tetiklenirse havada takla atıp sırtüstü düşüyor. Gerçek sinek bu durumda kanatlarıyla toparlanır. Bizim sineğimiz toparlanamıyor, sırtüstü de doğrulamıyor (Z-29).

### Z-27 · Nöral karar ile görünen hareketin tutarlılığı 🔴

Instagram eylemleri nöral okumadan seçiliyor, gövde aynı nöronlarla hareket ediyor (K-020). Yine de iki tutarsızlık olasılığı var:
- **İlgi kaybı:** Hiçbir kanal eşiği aşmadığında feed kayıyor, ama gövdede buna karşılık gelen bir hareket yok.
- **İleri kanalı:** Bacak motor nöronlarının toplamını okuyor. Sinek yürümeden (ör. yerinde kıpırdanarak) bu eşiği aşabilir.

- **Faz 4 okumasında bir hata:** TTMn ve STTMm (sıçrama kasları), kanat alt sınıfında oldukları için "yorum" kanalında sayılıyor. Oysa gövdede sıçrama üretiyorlar; "çıkış" kanalına taşınmalılar (yeniden kalibrasyon gerekir).

**Çözüm yolu:** Her kararda ilgili gövde bölgesinin hareketini ölçüp raporlamak. Örtüşmeyen durumlar veriye bakılarak kullanıcıyla birlikte çözülecek.

### Z-28 · Görselleştirme verisinin boyutu ve canlı izleme 🔴

- **Veri hacmi:** 165 bin nöronun spike'ları, 126 eklemin açıları ve ekran kareleri, saniyede yüzbinlerce olay demek.
- **Hız:** Simülasyon gerçek zamandan yavaş.

**Çözüm yolları:**
- Sıkıştırılmış oturum kaydı ve gerçek hızda oynatma.
- Canlı modun ağır çekim olarak açıkça etiketlenmesi.
- Beyin görünümünde spike'ların kısa zaman kutularında toplanması.

### Z-29 · Duruş tonusu yok 🔴

Gerçek sinekte yavaş motor nöronlar dururken de tonik ateşleyerek duruşu korur. Bizim modelde dinlenen beyin tamamen sessiz. Kas modelinin pasif sertliğiyle sinek çömeliyor (göğüs 0,68 mm); sıçramadan sonra sırtüstü kalırsa doğrulamıyor.

**Çözüm yolları:**
- Gövdeden gelen his: yük ve eklem açısı refleksleri tonik aktivite üretebilir.
- Sinir sistemindeki kendiliğinden aktivite: biyolojik gürültü (ilke 4). Kanıta dayanıyorsa eklenebilir.

### Z-30 · Şeker tadı tam hortum uzatma üretmiyor 🟡

Uçtan uca testte şeker tadı hortum nöronlarına ulaşıyor. Ama en çok çalışanlar arasında hortumu geri çeken MN2Da da var. Haustellum açılıyor (0,32 rad), rostrum ileri gitmiyor.

- **Karşılaştırma:** Shiu ve ark. modelinde şeker → MN9 güçlüydü.
- **Olası neden:** K-011 ayarında (düşük ağırlık, depresyon) MN9 yanıtı zaten zayıf (3,7 Hz).
- **Bağlam:** Gerçek sinekte hortum uzatma, açlık durumuna da bağlıdır; bu durum modellenmiyor.

---

## Instagram zorlukları

### Z-10 · Otomasyon kullanım şartlarına aykırı 🔴

Instagram, otomatik beğeni, takip ve yorumu yasaklıyor. Hesap kısıtlanabilir ya da kapatılabilir.

**Çözüm yolları:**
- Ayrı, bu projeye özel bir hesap kullanmak.
- **Güvenlik valisi:** saatlik ve günlük eylem sınırları, eylemler arası insan benzeri bekleme süreleri. Vali eylemi yalnızca engelleyebilir, seçemez.
- Görünür (headful) tarayıcı ve kalıcı oturum kullanmak; her seferinde yeniden giriş yapmamak.
- İlk haftalarda "ısınma" dönemi: düşük eylem sınırlarıyla başlamak.

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
