# Karar Kaydı

Projede alınan her tasarım kararı burada tutulur. Kararın bağlamı, seçenekleri ve gerekçesi de yazılır. Bir karar değişirse eski kayıt silinmez; "yerine geçti: K-xxx" notu eklenir.

Durumlar: **önerildi** · **kabul edildi** · **yerine geçti**

---

## K-001 · Veri seti: MaleCNS v1.0

- **Durum:** kabul edildi (2026-09-16)
- **Bağlam:** İki tam beyin konnektomu var: FlyWire FAFB v783 (dişi, yalnızca beyin, 2024) ve MaleCNS v1.0 (erkek, beyin + optik loblar + ventral sinir kordonu, 2026).
- **Seçenekler:**
  - FlyWire: simülasyonu yayınlanmış ve doğrulanmış, fakat bacak ve kanat motor nöronlarını içermiyor.
  - MaleCNS: motor çıktıların tamamı ve erkeğe özgü kur devreleri mevcut; üzerinde henüz yerleşik bir simülasyon yok.
- **Gerekçe:** Takip etme (P1) ve yorum yapma (kur şarkısı) eylemleri erkek sinek devrelerine dayanıyor. Ventral sinir kordonu da gerçek motor çıktısını mümkün kılıyor. FlyWire gerekirse doğrulama için yedek olarak tutulur.

## K-002 · Nöron modeli: Shiu ve ark. LIF

- **Durum:** kabul edildi (2026-09-16)
- **Gerekçe:** Tüm beyin ölçeğinde deneysel olarak doğrulanmış tek yaygın model; parametreleri yayınlanmış, dizüstü bilgisayarda çalıştırılabilir.

## K-003 · Eğitilmiş yorumlayıcı ve dil modeli yok

- **Durum:** kabul edildi (2026-09-16)
- **Gerekçe:** Projenin temel iddiası kararları sineğin vermesi. Nöral çıktıyı eğitilmiş bir ağ yorumlarsa kararı o ağ vermiş olur. Ayrıntı: [01-vizyon-ve-ilkeler.md](01-vizyon-ve-ilkeler.md).

## K-004 · Post görseli: nöral portre + yürüyüş resmi, seçim sinekte

- **Durum:** kabul edildi (2026-09-16)
- **Seçenekler:** nöral portre / yürüyüş resmi / sinek güdümlü üretken model / ilk ikisinin karışımı
- **Karar:** İlk ikisinin karışımı. İkisi de %100 sinek üretimi. Bir postta hangisinin kullanılacağını da sineğin o anki nöral durumu belirler (kural Faz 9'da kesinleşecek; K-022 ile yeniden numaralandı).
- **Elenen:** Üretken model, çünkü çizimi sinek değil model yapıyor.

## K-005 · Caption: koku-kelime seçimi

- **Durum:** kabul edildi (2026-09-16)
- **Seçenekler:** koku-kelime seçimi / kur şarkısı → Mors / ikisi birlikte
- **Karar:** Koku-kelime seçimi. Sinek feed'de karşılaştığı kelimeleri koku olarak algılar, caption yazarken en çok yaklaşma tepkisi verdiği kelimeleri sırayla seçer.

## K-006 · Instagram bağlantısı: tarayıcı otomasyonu

- **Durum:** kabul edildi (2026-09-16)
- **Seçenekler:** tarayıcı otomasyonu (Playwright) / hibrit (paylaşım resmi API ile) / instagrapi
- **Karar:** Playwright. Sinek ekranın kendisini "görür"; giriş kullanıcı tarafından elle yapılır ve kod şifre görmez.
- **Risk:** Kullanım şartlarına aykırı. Güvenlik valisi ve insan hızında çalışma ile hafifletilecek (Z-10, Z-11).

## K-007 · Güvenlik valisi yalnızca veto eder

- **Durum:** kabul edildi (2026-09-16)
- **Gerekçe:** Hesabı korumak için hız sınırları şart. Valinin eylem *seçmesine* izin verilirse ilke 1 bozulur; bu yüzden yetkisi engellemekle sınırlı.

## K-008 · Nörotransmitter → sinaps işareti

- **Durum:** kabul edildi (2026-09-16), modülatörler için varsayım
- **Kural:**
  - asetilkolin **+**; GABA, glutamat ve histamin **−**
  - dopamin, serotonin ve oktopamin **+** (varsayım)
  - Konsensüs tahmini "belirsiz" ise tekil tahmin kullanılır; o da belirsizse **+**
- **Gerekçe:** Asetilkolin, GABA ve glutamat için Shiu ve ark. ile aynı kural uygulanıyor. Histamin, fotoreseptörlerin vericisi ve postsinaptik klor kanalı açtığı biliniyor. Modülatörlerin etkisi reseptöre göre değişiyor; tek bir işaret seçmek zorunlu bir basitleştirme. Bu nöronlar toplamın yalnızca %0,3'ü.
- **Kod:** `flybrain/connectome/build.py` → `SIGN`

## K-009 · Bağlantı eşiği: en az 5 sinaps

- **Durum:** kabul edildi (2026-09-16)
- **Gerekçe:** Tek sinapslı bağlantıların önemli kısmı tespit hatası olabilir. 5 eşiği sinapsların %72'sini koruyor, bağlantı sayısını 25,6 milyondan 6,2 milyona indiriyor. Referans modellerle de uyumlu. Parametre olarak değiştirilebilir (`--min-synapses`).

## K-010 · Aday nöronların MaleCNS karşılıkları

- **Durum:** kabul edildi (2026-09-16); davranışsal doğrulama Faz 2 ve Faz 4'te
- **Eşleşmeler:** oDN1 → `DNg97`; aDN1 → `DNg62`; aDN2 → `DNge078`; P1 → `pC1_*` (fru+dsx yüksek); şeker GRN → `LB3b`, `LB3c`; acı GRN → `LB1a–d`
- **Kaynak:** Anotasyon tablosundaki `synonyms` ve `fruDsx` sütunları; şeker/acı eşlemesi için 2026 tam tat konnektomu çalışması. Ayrıntı: [05-veri-kesfi.md](05-veri-kesfi.md).

## K-011 · Beynin çalışma ayarı

- **Durum:** kabul edildi (2026-09-16), **B seçildi**
- **Bağlam:** Orijinal Shiu ağırlıklarıyla MaleCNS, girdiden bağımsız, kalıcı bir çekiciye kilitleniyor (Z-06). Ağırlık ölçeği ve iki biyolojik mekanizma (sinaptik depresyon ve ateşleme hızı adaptasyonu) 35 ayarda tarandı. Ayrıntılar: [06-simulasyon.md](06-simulasyon.md).
- **Ölçütler:**
  1. **Kararlılık:** uyarım sonrası kalıcı aktivite yok.
  2. **Ayırt edilebilirlik:** farklı kokular, inen nöronlarda farklı desenler üretmeli.
  3. **Biyolojik doğrulama:** şeker MN9'u ateşletmeli, acı ateşletmemeli.
- **Finalistler** (16 koku × 6 deneme):

| Aday | Kararlı | Koku ayırt edilebilirliği | Şeker→MN9 doğrulaması |
|---|---|---|---|
| A: ölçek 0,45 + STD 0,1 | ✅ | %82 | ❌ |
| B: ölçek 0,70 + STD 0,2, duyu muaf | ✅ | %62–64 | ✅ (3,7 Hz / 0 Hz; zayıf ama seçici) |
| C: ölçek 0,55 + STD 0,2, duyu muaf | ✅ | %86–89 | ❌ |

- **Öneri: B.** Gerekçeler:
  - Modelin bilinen tek biyolojik doğrulamasını koruyan tek aday bu. Projenin "bu gerçekten çalışan bir sinek beyni" iddiasının dayanağı bu doğrulama.
  - Ayırt edilebilirlik daha düşük olsa da şans düzeyinin yaklaşık 10 katı. Instagram kararları 16'lı ince bir sınıflandırma değil, kaba farklar gerektiriyor.
  - Görme sinyali çok katmanlı bir yoldan geçecek (Z-02). Daha güçlü ağırlıklar sinyalin sönmeden merkezi beyne ulaşma şansını artırıyor.
  - "Beğen = hortum" eşlemesi (Z-04) ancak bu adayda çalışabilir.
- **Karar:** B. Kodda `flybrain.sim.BRAIN_PARAMS` (ağırlık 0,275 × 0,70 mV; STD U = 0,2, τ = 800 ms; duyu nöronları muaf). `LIFParams()` varsayılanları Shiu ayarı olarak korunuyor.
- **Güvence:** [`tests/test_brain_params.py`](../tests/test_brain_params.py) bu ayarda şekerin MN9'u ateşlettiğini, acının ateşletmediğini ve beynin sönüp dinlenime döndüğünü her test çalıştırmasında doğruluyor.
- **Yeniden değerlendirme:** Faz 3'te görme sinyali ölçüldüğünde bu karar tekrar gözden geçirilecek.
- **Ek (2026-09-16, Faz 3):** Kodlayıcının doğrudan sürdüğü giriş nöronları da (ör. görmede L2, L3, Mi1, Tm3) depresyondan muaf tutuluyor (`Simulator(std_exempt=...)`). Gerekçe duyu nöronlarıyla aynı: bu nöronların Poisson hızı zaten etkin girdiyi temsil ediyor. Muafiyet olmadan görme sinyali optik lobdan çıkamıyordu ([07-duyular.md](07-duyular.md)).

## K-012 · Görme girişi: ON/OFF kontrast kodlaması, 250 Hz

- **Durum:** kabul edildi (2026-09-16)
- **Bağlam:** Fotoreseptörler ketleyici olduğu için sessiz modelde doğrudan uyarılmaları işe yaramıyor (Z-02).
- **Seçenekler:**
  - **off:** karanlık → L2, L3
  - **onoff:** off + aydınlık → Mi1, Tm3
  - **foto:** ışık → fotoreseptörler, ayrıca lamina ve ON nöronlarına tonik akım
- **Sonuçlar:**
  - Yalnızca **onoff** sinyali merkezi beyne ve inen nöronlara taşıyor.
  - **foto**, gri ekranda bile yaklaşık 15 bin nöronu sürekli ateşletiyor ve sinyali merkeze ulaştıramıyor.
  - onoff 250 Hz, 16 doğal istatistikli görseli %95–100 ayırt ediyor. Gri ekranda sessiz, görsel sonrası dinlenime dönüyor.
- **Karar:** onoff, doymuş kontrastta 250 Hz. Kontrast `c = (I − Ī)/Ī`, 0,6'da doyuyor. Gri ekran sıfır uyarım demek.
- **Bedel:** Fotoreseptör katmanı ve renk kanalları (R7/R8) kullanılmıyor; renk yalnızca parlaklık ağırlıklarıyla (R 0,05, G 0,55, B 0,40) etkiliyor. foto yöntemi kodda duruyor; ileride tonik aktiviteyle birlikte yeniden denenebilir.
- **Kod:** `flybrain/senses/vision.py`; deney: `flybrain/experiments/vision.py`

## K-013 · Kelime → koku eşlemesi

- **Durum:** kabul edildi (2026-09-16)
- **Kural:**
  - Her kelime (ya da emoji) 53 glomerülden 3'üne eşlenir. Eşleme blake2b özetine dayanan sabit bir sıralamayla (rendezvous hashing) yapılır.
  - Karışımda glomerül etkinliği, onu seçen kelime sayısıdır: `hız = 200 · a / (a + 1/3)` Hz. Tek kelime 150 Hz verir.
  - En fazla 40 kelime kullanılır.
- **Gerekçe:** Eşleme sabit ve anlamdan bağımsız; sinek anlamı değil kokuyu ayırt ediyor. Yoğunluk, Faz 2'de ayırt edilebilirliği ölçülen yapay kokularla aynı.
- **Ölçüm:** Görselle birlikte verildiğinde 4 caption %52 doğrulukla ayırt ediliyor (şans %25).

## K-014 · Panoramik gösterim

- **Durum:** kabul edildi (2026-09-16)
- **Kural:** Post görseli sineğin tüm görme alanına yayılır. Görselin sol yarısı sol göze, sağ yarısı sağ göze düşer; orta çizgi tam önü, kenarlar en arka kolonları, üst kenar sırt yönünü gösterir.
- **Alternatif:** Görseli yalnızca ön görme alanındaki küçük bir pencereye, gerçek bir ekran gibi yerleştirmek. Bu durumda çok az kolon uyarılırdı.
- **Gerekçe:** Postu sineğin gözünün tamamıyla "görmesi" en zengin girdiyi sağlıyor. Görme yönleri lamina geometrisinden çıkarıldı ([07-duyular.md](07-duyular.md#göz-geometrisi)).

## K-015 · Motor okuma: kas grupları

- **Durum:** kabul edildi (2026-09-16)
- **Bağlam:** Literatürdeki komut nöronları (DNp09/oDN1, MN11/12, P1, aDN) gerçekçi postlarda hiç ateşlemedi. Bu haliyle sinek feed'i hiç kaydıramazdı ([08-motor.md](08-motor.md)).
- **Karar:** Okuma, motor nöronların ve inen nöronların hedeflediği vücut bölgesine (MaleCNS `subclass`) göre gruplanmış kas kanallarından yapılır:

  | Kanal | Eylem | Nöronlar |
  |---|---|---|
  | ileri | sonraki post | bacak MN'leri |
  | geri | önceki post | MDN |
  | hortum | beğen / kaydet | hortum MN'leri |
  | yorum | yorum yap | kanat yönlendirme MN'leri |
  | takip | takip et | karın MN'leri |
  | cikis | takipten çık / oturumu bitir | alt tectulum inen nöronları |
  | sekme | sekme değiştir | boyun MN'lerinde sol − sağ farkı |
  | timar | boşta bekle | ön bacak − diğer bacaklar |

- **Gerekçe:** Bu gruplar her postta aktif, tutarlı ve içeriğe duyarlı. Eşleme sabit ve anatomik; eğitilmiş bir yorumlayıcı yok (K-003 korunuyor).
- **Kod:** `flybrain/motor/readout.py`

## K-016 · Eylem bütçesi

- **Durum:** kabul edildi (2026-09-16), kullanıcı kararı
- **Seçenekler:**
  - **ham:** hep yorum ya da çıkış
  - **nötr z-skor:** tüm eylemler eşit sıklıkta
  - **eylem bütçesi**
- **Karar:** Eylem bütçesi. Genel sıklıkları insan belirler; hangi postta hangi eylemin yapılacağını sinek seçer. Bütçe:

  | Kanal | ileri | geri | hortum (beğen + kaydet) | yorum | takip | çıkış | sekme | tımar |
  |---|---|---|---|---|---|---|---|---|
  | Bütçe | %35 | %3 | %15 | %2 | %2 | %2 | %5 | %5 |

  Hiçbir kanal eşiğini aşmazsa sinek 1,5 saniye sonra "ilgisini kaybeder" ve kaydırır.
- **Kalibrasyon:** Eşikler, içerikten bağımsız 480 referans posttan çıkarılır. Her kanalın z-skoru, pencere sırasına göre ayrı ortalama ve standart sapmayla hesaplanır. Standart sapmaya, tek bir spike'ın yarattığı hız kadar bir taban uygulanır (sayma gürültüsü).
- **İlke notu:** [01-vizyon-ve-ilkeler.md](01-vizyon-ve-ilkeler.md) kalibrasyonu yalnızca nötr uyaranla (gri ekran) sınırlamıştı. Gri ekranda bütün kanallar tam olarak sıfır olduğu için ölçek oradan çıkarılamıyor. Bunun yerine içerikten bağımsız referans postlar (rastgele doku + rastgele kelimeler) kullanılıyor. İlke değişikliği vizyon belgesine işlendi.
- **Kod:** `flybrain/motor/selector.py`, `flybrain/motor/calibration.json`, `flybrain/experiments/calibrate.py`

## K-017 · Takip et = karın kasları

- **Durum:** kabul edildi (2026-09-16), kullanıcı kararı
- **Bağlam:** P1 nöronları hiçbir postta ateşlemedi.
- **Karar:** Takip et, karın motor nöronlarına bağlanır. Erkek sineğin kur yapmasının son aşaması karın bükmedir (çiftleşme girişimi).

## K-018 · Beğen ve kaydet: aynı kanal, iki şiddet

- **Durum:** kabul edildi (2026-09-16), kullanıcı kararı. Kullanıcı özellikle istedi: "çoğu hortum tepkisi kaydetmeye gitmesin; orta ve yüksek şiddet eşikleri bilinçli belirlensin."
- **Bağlam:** Yutma nöronları (MN11/12) hiç ateşlemedi.
- **Karar:**
  - **Beğeni:** hortum kanalı, referans postların üst %15'inde aşılan eşiği geçerse.
  - **Kaydetme:** hortum kanalı, üst %2'de aşılan eşiği geçerse. Bu eşik ayrıca beğeni eşiğinin en az 1 standart sapma üstünde olmak zorunda.
  - **Hedef:** hortum eylemlerinin yaklaşık %13'ü kaydetme olmalı.
  - Gerçekleşen oran ayrı test postlarında ölçülüp raporlanır ([08-motor.md](08-motor.md)).

### K-016 eki: kalibrasyon yöntemi ve eşik homeostazı (2026-09-16)

- **Kalibrasyon yöntemi:**
  - Birikimli kanıt ve sayma gürültüsü tabanı.
  - Eşikler, karar kuralı referans postlarda bütünüyle uygulanarak gerçekleşen oranlara göre belirleniyor.
- **Eşik homeostazı:** Sabit eşiklerle ayrı postlarda gerçekleşen oranlar bütçenin altında kaldı (beğeni + kaydet %7,8'e karşı %15). Bu yüzden kullanımda eşikler her karardan sonra 0,05 z adımla bütçeye doğru kaydırılıyor.
- **Kaydetme denetleyicisi:** Yalnızca hortum kararlarında çalışıyor, bu kararlar içindeki kaydetme payını ~%13'e çekiyor (adım 0,15 z) ve beğeni eşiğinin en az 1 standart sapma üstünde kalıyor. İlk sürüm (tüm postlarda, bütçe %2) çok yavaş kaldı ve 720 bakışta hiç kaydetme üretmedi.
- **Sınır:** Homeostaz yalnızca genel sıklığı etkiliyor; postlar arasındaki tercih sıralaması sinekte kalıyor.
- **Ayrıntılar ve ölçümler:** [08-motor.md](08-motor.md#6-kalibrasyon-ve-doğrulama).

## K-019 · 3D gövde: NeuroMechFly, doğrudan motor nöron → kas → eklem

- **Durum:** kabul edildi (2026-09-17), kullanıcı isteği
- **Bağlam:** Kullanıcı sineği 3D olarak görmek istiyor: yürümesini, Instagram kullanmasını, korkup kaçmasını ve beyin aktivitesini. Şartı açık: "animasyon, fake simülasyon, deterministik kod gibi sineğin karar vermediği bir çözüm değil; bire bir sineğin davranışlarını görmek istiyoruz."
- **Seçenekler:**
  - **Hazır kontrolcüler:** Beyinden birkaç inen nöron okunur, bunlar eğitilmiş yürüme/tımar programlarını tetikler. Eon Systems demosu (Mart 2026) böyle çalışıyor. Hareketi sinek üretmediği için reddedildi.
  - **Beyin karar verir, adım ritmini hazır osilatör üretir:** Adım deseni sineğin değil; kullanıcı şartına aykırı.
  - **Doğrudan:** Motor nöron spike'ları → kas aktivasyonu → eklem torku → fizik. Gövdeden gelen his beyne geri döner.
- **Karar:** Doğrudan yol.
  - **Gövde:** NeuroMechFly v2 (FlyGym 2.1, Apache-2.0, MuJoCo), 126 eklem serbestlik derecesi.
  - **Eşleme:** Motor nöron tipi → kas → eklem tablosu anatomi literatürüne dayanır; davranışa bakılarak ayarlanmaz.
  - **Kusurlar:** Hareket kusurluysa kusurlu gösterilir. Düzeltmeler yalnızca biyolojik gerekçeyle yapılır ve belgelenir.
- **Neden mümkün:** MaleCNS sinir kordonunu ve kasa göre etiketli motor nöronları içeriyor. Pugliese ve ark. (2025), yürüme ritminin sinir kordonu konnektomundan eğitimsiz olarak çıktığını gösterdi.
- **Ayrıntılar:** [09-govde.md](09-govde.md)

## K-020 · Instagram eylemleri nöral okumadan; gövde aynı nöronlarla, tutarlılık ölçülür

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı. Kullanıcının notu: "nöronlardan okuyalım, ama sineğin hareketleri de örtüşsün, tutarsızlık olmasın."
- **Seçenekler:**
  - **Fiziksel:** Yürünen mesafe feed'i kaydırır, hortum açısı beğeniyi belirler.
  - **Nöral okuma + gövde:** Faz 4'teki kas grubu okuması korunur, gövde aynı motor nöronlarla paralel hareket eder.
- **Karar:** Nöral okuma + gövde. İki çıktı aynı spike'lardan gelir.
- **Güvence:** Her kararda ilgili gövde bölgesinin hareket edip etmediği ölçülür ve raporlanır. Örtüşmeyen durumlar (ilgi kaybı, yürümeden ileri kararı) Z-27'de izlenir ve kullanıcıyla birlikte çözülür.

## K-021 · Sahne: serbest sinek, onu izleyen ekran

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Seçenekler:**
  - Top üzerinde bağlı sinek (klasik laboratuvar düzeni)
  - Serbest sinek + onu izleyen sanal gerçeklik yüzeyi (FreemoVR benzeri; Stowers ve ark. 2017)
- **Karar:** Serbest sinek. Instagram ekranı sineğin önünde bir yüzeyde gösterilir ve sineğin konumunu izler. Kaçışta sinek gerçekten sıçrayıp uzaklaşabilir; yeniden yerleştirilmesi gerekmez.
- **İlke notu:** Ekranın sineği izlemesi "dünyanın fiziği" kategorisinde bir insan kararıdır; sineğin kararlarına dokunmaz.

## K-022 · Yol haritası: önce gövde ve görselleştirme

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Karar:** Yeni sıra:
  - Faz 5: gövde
  - Faz 6: görselleştirme ve kayıt
  - Faz 7: yerel kum havuzu ve korku tepkisi
  - Faz 8: Instagram bağlantısı
  - Faz 9: içerik üretimi
  - Faz 10: öğrenme ve uzun dönem çalışma
- **Sonuç:** Instagram bağlantısı iki faz ertelendi.
- **Kayıt ve oynatma:** Simülasyon gerçek zamandan yavaş olduğu için her oturum kaydedilir ve gerçek hızda oynatılabilir. Oynatma animasyon değildir: her spike ve her eklem açısı simülasyondan gelir ve olduğu gibi gösterilir. Canlı mod ise ağır çekimdir.

### K-019 eki: kas modeli (2026-09-17)

- **Bacak kas geometrisi:** FlyGym içindeki kas-iskelet modelinden (FlyMimic; sol ön bacak, 15 kas) moment kolları, kuvvetler, pasif özellikler ve açı aralıkları okunuyor. Kas adları konnektomdaki motor nöron tipleriyle aynı.
- **Diğer bacaklar:** Aynı geometri, nötr açıya göre kaydırılmış aralıklarla uygulanıyor (bacakların yapısal benzerliği varsayımı).
- **Hareket yönleri:** Elle yazılmıyor; NeuroMechFly'ın nötr pozunda geometriden çıkarılıyor (`flybrain/body/derive.py`).
- **Fizyolojik sınırlar:** Boy–kuvvet sınırı (tamamen kısalmış kas kuvvet üretmez) ve sert eklem sınırları eklendi. Bunlar olmadan kas torkları eklemleri anatomik aralığın dışına taşıyordu.
- **Kaynaksız parametreler:** Her biri [09-govde.md](09-govde.md#65-varsayımlar-kaynağı-olmayan-parametreler) içinde listeli. Hareketin biçimini ve genliğini etkiliyorlar, zamanlamasını değil.

## K-023 · Ölçülmüş elektriksel sinapslar modele eklenir

- **Durum:** kabul edildi (2026-09-17)
- **Bağlam:**
  - Konnektomda dev liften TTMn'ye kimyasal sinaps var (sağ 70, sol 20). Ama tek dev lif spike'ı TTMn'de yaklaşık 2 mV yaratıyor; eşik farkı 7 mV.
  - Depresyon yüzünden 150 ms'lik sürekli uyarımda bile TTMn ateşlemedi, yani kaçış devresi çalışmıyordu.
  - Gerçek sinekte bu bağlantı elektriksel sinapsla 1:1 çalışır (Tanouye ve Wyman 1980; Allen ve ark. 2006). Elektriksel sinapslar elektron mikroskobu konnektomunda görünmez.
- **Karar:** Literatürde ölçülmüş ve davranış için kritik elektriksel sinapslar `flybrain/connectome/electrical.py` içindeki listeye eklenir. Şimdilik iki bağlantı var: dev lif → TTMn ve dev lif → PSI.
  - **Eşleşme:** Kimyasal sinapslarla aynı tarafta.
  - **Ağırlık:** Ölçülen 1:1 iletimi sağlayacak şekilde nöron modelinin denkleminden hesaplanıyor: tek olayın tepe gerilimi, eşik farkının 2 katı (462 sinaps eşdeğeri).
  - **Depresyon:** Presinaptik nöronlar muaf, çünkü elektriksel sinaps vezikül tüketmez.
- **Kapsam:** Şimdilik yalnızca gövdeli sinekte (`EmbodiedFly`) kullanılıyor. Instagram'a karar veren `Fly` sınıfına gövdeyle birlikte geçecek; bu geçiş yeniden kalibrasyon gerektiriyor.

## K-024 · Propriyoseptörlerin kimliği bağlantı imzasından, kodlaması ölçülmüş işlevden

- **Durum:** kabul edildi (2026-09-17)
- **Bağlam:**
  - MaleCNS, bacak propriyoseptörlerini pençe/kanca/topuz ve kıl plakası olarak etiketliyor. Ama pençe ve kancanın bükülmeye mi açılmaya mı, kıl plakalarının hangi eklemin hangi sınırına duyarlı olduğunu vermiyor.
  - Bu bilgi olmadan eklem durumu doğru nöronlara iletilemez. Yön ters olursa refleks, olumsuz geri bildirim yerine olumlu geri bildirime döner.
- **Karar:**
  - **FeCO:** Bükülme/açılma ataması, Lee ve ark. (2025) FANC'ta bildirdiği bağlantı imzasıyla yapılır. Bükülme algılayıcıları tibia açıcı motor nöronlarını doğrudan uyarır ve bükücüleri dolaylı ketler; açılma algılayıcıları tersini yapar. İmza MaleCNS'te her tip için ölçülür ve testle korunur. SNpp50 bükülme pençesi, SNpp51 açılma pençesi, SNpp41 bükülme kancası, SNpp39 açılma kancası.
  - **Kıl plakaları:** Pratt ve ark. (2026) CxHP8'de ölçülen düzen genellenir (VARSAYIM): plaka, doğrudan uyardığı kasların hareketinin tersindeki eklem sınırında ateşler.
  - **Kodlama:** Pençe ve plaka tonik pozisyon, kanca yönlü hız, topuz iki yönlü hız kodlar (Mamiya ve ark. 2018). Eşikler grup içinde aralığa yayılır.
  - **Kaynaksız sayılar:** En yüksek hız ve hız eşikleri gibi değerler [09-govde.md](09-govde.md#75-varsayımlar) içinde listelenir; davranışa bakılarak ayarlanmaz.
- **Dışarıda kalanlar:**
  - Yük algılayıcıları ve tarsal temas: etiket eksik.
  - Yönü belirsiz kordotonal tipler.
  - Boyun kıl plakaları: bağlantıları çelişkili.
- **Sonuç:** Refleks yönü doğrulandı. Refleks genliği zayıf (Z-31); ön bacaklarda veri eksik (Z-32).

## K-025 · Sinir kordonu için hız modeli (Pugliese ve ark.) — deneysel

- **Durum:** kabul edildi, deneysel (2026-09-17). Varsayılan model şimdilik tamamen LIF.
- **Bağlam:** LIF ayarında bacak motor nöronları yürüme komutu altında 2–8 Hz'de kalıyor ve kazancı artırmak koordinasyon getirmiyor (Z-31). Bu konnektomda yürüme ritmini gösteren tek çalışma (Pugliese ve ark. 2025) nöron boyutuna göre ölçeklenmiş, hız tabanlı bir model kullanıyor.
- **Kullanıcı kararı:** "Sinir kordonu hıza dayalı model" (seçenekler: hız modeli / LIF'i ayarlamak / yürümeyi ertelemek).
- **Uygulama:**
  - **Model:** `flybrain/sim/rate.py`. Denklem ve parametreler makaledeki gibi; kod yazarların deposundan kopyalanmadı, makaleden yeniden yazıldı.
  - **Nöron boyutu:** MaleCNS neuPrint girdi tablosundan, dosyanın tamamı indirilmeden (HTTP aralık istekleri, ~4 MB) okundu. Kullanıcı izniyle: `flybrain/connectome/sizes.py`.
    - Sinaps sayısı boyut vekili olarak denendi. Sıra korelasyonu 0,925 olmasına rağmen ritmi tamamen yok etti.
  - **Ağ:** Yazarların seçim ölçütü (motor nöronlar, onlara en az bir sinaps yapanlar, bunlara sinaps yapan inen nöronlar) altı bacağa uygulandı: `connectome/motor_network.py`. Kanat, karın ve boyun ağları eklenince model kendini sürdüren doygun bir duruma geçiyor; bu ağlar LIF'te kaldı.
  - **Melez:** `sim/hybrid.py`. Beyin ve inen nöronlar LIF, bacak motor ağı hız modeli. İnen nöron spike'ları 300 ms'lik süzgeçle hıza çevriliyor.
- **Doğrulama:** Yazarların MaleCNS ön bacak deneyi yeniden üretildi: koşuların %98'i salınıyor, 11 Hz.
- **Neden deneysel:**
  - Ritim rejiminde bacak motor nöronu hızları 1–6 Hz; gövde neredeyse kıpırdamıyor.
  - Güçlü girdide ağ doyuma kilitleniyor (motor nöronlar 200 Hz).
  - Propriyosepsiyonun hız modelindeki ölçeği kalibre edilmemiş: dinlenmede bile ağı doyuruyor.
  - Ayrıntılar: [09-govde.md](09-govde.md#8-sinir-kordonu-hız-modeli-2026-09-17), Z-33. Sonraki yön kullanıcıya soruldu.

## K-026 · Yürüme ertelendi; önce görme, sahne ve görselleştirme

- **Durum:** kabul edildi (2026-09-17)
- **Bağlam:** Hız modeli ritmi yeniden üretiyor, ama gövdeyi yürütmesi için motor çıktı, doyum ve duyu kazancı sorunları var (Z-33). Bunların çözümü, çoğu için doğrudan ölçümü olmayan kalibrasyonlar gerektiriyor.
- **Kullanıcı kararı:** "Yürümeyi ertele" (seçenekler: ertele / modeli ayarla / önce yorulma ekle).
- **Sonuç:**
  - Varsayılan model LIF kalıyor; hız modeli `vnc="rate"` ile deneysel olarak duruyor.
  - Sıradaki işler:
    1. sineğin kendi gözleriyle görmesi,
    2. Instagram ekranlı sahne,
    3. beyin aktivitesi ve kayıt paneli (Faz 6).
  - Yürümeye sonra dönülecek.
