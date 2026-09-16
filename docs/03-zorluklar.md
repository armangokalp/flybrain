# 03 — Zorluklar ve Çözüm Yolları

Bu belge yaşayan bir belgedir. Yeni bir sorunla karşılaştıkça buraya eklenir, çözüldükçe durumu güncellenir.

Durum etiketleri: 🔴 açık · 🟡 üzerinde çalışılıyor · 🟢 çözüldü

---

## Bilimsel zorluklar

### Z-01 · Konnektom kabloları veriyor, sinaps güçlerini vermiyor 🔴

Haritada hangi nöronun hangisine kaç sinapsla bağlandığı var. Sinapsın ne kadar güçlü olduğu ve bazı durumlarda uyarıcı mı ketleyici mi olduğu yok.

**Çözüm yolu:** Shiu ve ark. modelinin varsayımını kullanıyoruz: her sinaps eşit ağırlıkta, işaret ise nörotransmitter tahmininden geliyor. Bu model tat devrelerinde deneysel olarak doğrulandı. Aynı doğrulamayı MaleCNS üzerinde tekrarlayacağız (şeker nöronlarını uyar, MN9 ateşliyor mu bak). Tutmazsa global ağırlık ölçeğini ayarlayacağız. Bu ayar yalnızca "beyin canlı ama epileptik değil" koşulu için yapılacak.

### Z-02 · Görme sinyali merkezi beyne ulaşabilecek mi? 🟡

Fotoreseptörlerden inen nöronlara kadar birçok sinaptik katman var. Eşit ağırlık varsayımıyla sinyal bu katmanlarda sönebilir ya da kontrolden çıkabilir.

**Faz 1 bulgusu (2026-09-16):** Sorun beklenenden temel çıktı. Fotoreseptörler **histaminerjik**, yani ilk sinapsları ketleyici. Fotoreseptörlerden motor havuzlarına **hiç uyarıcı yol yok**. Shiu modelinde nöronlar uyarı yokken sessiz. Sessiz bir nöronu ketlemek hiçbir şey değiştirmediği için fotoreseptörleri doğrudan uyarmak **hiçbir aşağı akış aktivitesi üretmez**.

Gerçek sinekte böyle olmuyor: lamina nöronları ışıkta sürekli aktif ve ışık değişimleri bu aktiviteyi aşağı ya da yukarı kaydırıyor. Sinek gözü aslında büyük ölçüde **kontrast** algılıyor. Aynı sorun sonraki katmanlarda da tekrar ediyor (L1 glutamaterjik, dolayısıyla modelde ketleyici).

**Çözüm seçenekleri (Faz 3'te deneyle seçilecek):**
- **(a) Tonik taban aktivite:** Görme sistemine sürekli bir arka plan uyarımı verilir, görsel bu tabanın etrafında dalgalanma yaratır. Biyolojiye en yakın seçenek bu, fakat yeni bir parametre ekliyor (taban hızı).
- **(b) Kolon nöronlarından giriş:** İşaret dönüşümü elle uygulanır ve görsel, kolon koordinatı olan nöronlara (L2 uyarıcı; Mi1, Tm1...) verilir. Karanlık bölgeler L2'yi daha çok ateşler. Basit bir yöntem, ancak fotoreseptör katmanı atlanmış olur.
- **(c) İkisinin birleşimi.**

Her durumda kalibrasyon katman katman aktivite ölçümüyle yapılacak (fotoreseptör → lamina/medulla → lobula → merkezi beyin → inen nöronlar).

### Z-03 · Plastisite yok, dolayısıyla öğrenme de yok 🔴

LIF modelinde bağlantılar sabit. Sinek beğeni alsa bile bundan bir şey öğrenmez. Böyle kalırsa feed yalnızca Instagram'ın algoritması tarafından şekillenir.

**Çözüm yolu (Faz 8):** Mantar gövdesinde (mushroom body) dopaminle kapılanan bir öğrenme kuralı eklemek. Sinekteki öğrenmenin gerçek mekanizması bu: Kenyon hücresi → MBON sinapsları, dopamin sinyali geldiğinde zayıflar. Ödül (beğeni, takipçi) PAM nöronlarını uyarır; böylece sinek neyin ödül getirdiğini öğrenebilir.

### Z-04 · Sinek resim yemez: "beğen" hiç tetiklenmeyebilir 🔴

MN9 (hortum uzatma) gerçek sinekte asıl olarak **tat** ile tetiklenir, görüntüyle değil. Biyolojik olarak doğru bir model gördüğü görsele hortum uzatmayabilir.

**Çözüm yolları:** (a) Bunu kabul etmek: sinek nadiren beğenir ve bu durum da bir sonuçtur. (b) Kokunun (caption) beslenme devrelerini etkilemesine izin vermek. (c) "Beğen" eylemini bir yaklaşma davranışına bağlamak (hedefe dönme + ileri yürüme). Karar Faz 4'te, gerçek aktivite verisine bakılarak verilecek.

### Z-05 · Sinek okuyamaz 🔴

Caption'lar metin; sineğin dil diye bir yetisi yok.

**Çözüm yolu:** Kelimeleri kokuya çeviriyoruz (bkz. [mimari](02-mimari.md)). Bu eşleme keyfi fakat **sabit**. Sinek anlamı değil, kokuyu ayırt eder. Anlamlı bir metin beklemek gerçekçi değil; ortaya çıkacak şey sineğin "koku zevkini" yansıtan bir kelime dizisi.

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

### Z-07 · Hesaplama maliyeti 🔴

166.000 nöron, 0,1 ms adım: 1 saniyelik simülasyon 10.000 adım ediyor. Benzer bir NumPy uygulaması (FlyWire, 139 bin nöron) dizüstü bilgisayarda simülasyonun 1 saniyesi başına yaklaşık 8 saniye harcıyor.

**Çözüm yolları:**
- **Olay güdümlü güncelleme:** Her adımda nöronların yalnızca küçük bir kısmı ateşliyor. Bu yüzden seyrek matrisin yalnızca ateşleyen sütunlarını toplamak yeterli.
- Numba ile paralel çekirdek; Apple Silicon üzerinde PyTorch/MPS seçeneği de denenecek.
- **Zaman ayrıştırma:** Instagram gerçek zamanlı yanıt beklemiyor. Beyin hesap yaparken tarayıcı postta bekleyebilir. Bakma süresini duvar saati değil, simülasyon zamanı belirler.

Faz 2'de ölçüm yapılacak.

### Z-08 · Bellek ve disk 🟢

Makine: 16 GB RAM, yaklaşık 35 GB boş disk. Bağlantı tablosu 1 GB (feather); bellekte 3,5 GB'a çıkıyor (152 milyon satır).

**Çözüm:** Yalnızca gereken üç dosya indirildi (1,1 GB). 12,7 GB'lık sinaps noktaları dosyası indirilmedi. Tablo memory-map ile açılıp pyarrow ile süzülüyor. Önbellek üretimi 3 saniye sürüyor, bellek kullanımı en fazla 4,4 GB'a çıkıyor ve sonuç diskte 54 MB tutuyor.

### Z-09 · Görsel → ommatidyum eşlemesi 🟡

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

### Z-16 · Ağ çok sıkı bağlı: özgüllük nereden gelecek? 🔴

Her duyu, beynin yaklaşık %98'ine birkaç sinaptik adımda ulaşıyor. Şeker nöronları da, acı nöronları da, dopamin nöronları da her motor havuzuna 2–3 adımda erişebiliyor.

**Anlamı:** Hangi davranışın ortaya çıkacağını topoloji değil, sinaps sayıları ve işaretler belirleyecek. Uyarım çok güçlü olursa her şey ateşler ve davranış ayırt edilemez hale gelir.

**Çözüm yolu:** Faz 2'de uyarım yoğunluğuna karşı yanıt eğrileri çıkarılacak. Seçicilik ölçütü şöyle olacak: şeker MN9'u ateşletmeli, acı ateşletmemeli.

### Z-17 · Modülatör nörotransmitterlerin işareti belirsiz 🟡

Dopamin, serotonin ve oktopamin reseptöre göre uyarıcı da olabilir ketleyici de. Model tek bir işaret istiyor.

**Geçici çözüm:** Hepsi uyarıcı kabul edildi (K-008). Bu nöronlar toplamın %0,3'ü. Faz 8'de dopamin, öğrenme kuralındaki rolüyle (işaret yerine plastisite sinyali olarak) ayrıca modellenecek.

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
