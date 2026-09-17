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

## K-027 · Gövdeli sinekte görme: kolon başına örnekleme ve zamansal uyum

- **Durum:** kabul edildi (2026-09-17)
- **Bağlam:** Faz 3'teki görme kodlaması durağan bir görselin kontrastını sürekli ateşlemeye çeviriyordu. Gövdeli sinek durağan bir dünyaya bakınca bu, sürekli ~900 kHz'lik bir uyarım yarattı ve dev lif hiçbir şey hareket etmezken 63 Hz ateşledi.
- **Karar:**
  - **Örnekleme:** Sahne, sineğin başına bağlı iki kameradan çiziliyor ve konnektomdaki her kolon kendi bakış yönünden örnekleniyor. FlyGym'in ommatidyum ızgarası kullanılmıyor.
  - **Zamansal kodlama:** Her kolon kendi parlaklığına uyum sağlıyor (1 sn). Geçici hücreler (L2, Mi1, Tm3) kontrast değişimini, kalıcı hücreler (L3) kontrastı görüyor.
  - **Faz 3'e etki yok:** Panoramik post görselleriyle çalışan durağan kodlama (Fly sınıfı) değişmedi.
- **Sonuç:** Durağan sahne kaçışı tetiklemiyor. Değişen, hareket eden ve yaklaşan şeyler yanıt üretiyor; yaklaşan nesneye kaçış tepkisi (Faz 7) ayrıca sınanacak.
- **Açık:**
  - Geçici süzgecin zaman sabiti için kaynak bulunamadı.
  - Instagram kararları (K-020) gövdeli sinekte zamansal yanıtlarla yeniden kalibre edilmeli.

## K-028 · Sahne: sineğin önünde dikey, kavisli telefon ekranı

- **Durum:** kabul edildi (2026-09-17). Ekran boyu, izleme ve geçiş kullanıcı kararı; geometrinin ayrıntıları ölçümle seçildi. **Geçiş kısmı yerine geçti: K-030.**
- **Bağlam:** K-021 sahneyi "serbest sinek + onu izleyen ekran" olarak belirlemişti. Ekranın boyu, izleme biçimi ve post geçişi açıktı.
- **Karar:**
  - **Boyut (kullanıcı):** Önde geniş ekran, ama akıllı telefon oranında (9:19,5, dikey). Bu, K-014'teki tam panoramanın yerini alıyor.
  - **Geometri:** Başın düşey ekseni etrafında 180°'lik yay, 2 mm uzaklık. Yükseklik orandan geliyor (13,6 mm).
  - **Post konumu:** Görsel gezinme çubuğunun hemen üstünde (aşağı kaydırılmış akış).
  - **Yuva:** Telefon zemindeki bir yuvaya oturuyor; gezinme çubuğu ve alt çerçeve (0,95 mm) zeminin altında kalıyor.
  - **İzleme (kullanıcı):** Ekran başın konumunu ve göğsün yönünü 500 ms zaman sabitiyle izliyor.
  - **Geçiş (kullanıcı):** Sonraki posta gerçek kaydırmayla geçiliyor (400 ms, hızlı başlayıp yavaşlayan). *(Yerine geçti: K-030, solarak geçiş.)*
  - **Arena:** Gri; gökyüzü 0,5, zemin 0,40/0,45. Işık yukarıdan geliyor, kameraya bağlı ışık zayıf.
- **Gerekçe:**
  - **Görünen bölge:** Gözler 0,7 mm yüksekte ve kolonların en üstü ~75° yukarı bakıyor. Sinek dikey bir telefonun yalnızca alt ~%60'ını görüyor; post bu bölgeye konuldu.
  - **Yuva:** Yuva olmadan gezinme çubuğu, kolonların en yoğun olduğu ufuk bandına düşüyordu; postu kolonların %37'si görüyordu. Yuvayla bu oran %62.
  - **Neden yaklaştırılmadı:** Ekranı 1 mm'ye yaklaştırmak da işe yarıyordu (%66), ama ön bacak uçları başın ekseninden 1,35 mm öteye uzandığı için bacaklar ekranın içinden geçiyordu.
- **Sonuç ([09-govde.md](09-govde.md#11-telefon-ekranlı-sahne-2026-09-17)):**
  - Ekran kolonların %66'sını, post görseli %62'sini kaplıyor.
  - Kaydırma, sineği her geçişte kaçırıyor (12/12). Kullanıcı bunu modelin kendi öngörüsü olarak kabul etti (Z-35).
  - *Sonradan:* Kontroller kaçışın yaklaşmaya özgü olmadığını gösterdi (Z-25); "öngörü" çerçevesi geri çekildi ve geçiş değişti (K-030).
  - Ani değişim ve solarak geçiş deneyler için seçenek olarak duruyor.
- **İlke notu:** Ekranın izlemesi ve geçişin biçimi "dünya fiziği" kararları; sineğin kararlarına dokunmuyor.

## K-029 · Gövdeli sinekte görme kazancı 125 Hz

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Bağlam:**
  - K-012'deki 250 Hz, gövdesiz sinekte durağan bir postun sürekli kontrastı için seçilmişti.
  - Gövdeli sinekte zamansal kodlamayla (K-027) sineğin dinlenirken yaptığı küçük hareketler de görme uyarımı üretiyor.
  - 250 Hz'de telefona bakan sinek çoğu denemede bir saniye içinde kendiliğinden kaçıyordu (Z-34).
- **Seçenekler ve ölçümler (yaklaşan disk: l/v 40 ms):**

  | Kazanç | Yaklaşan diske kaçış | Durağan ekranda kendiliğinden kaçış |
  |---|---|---|
  | 250 Hz | 4/4 | 0,76 sn'lik denemelerin 6/8'inde |
  | 150 Hz | 18/18 | 0,76 sn: 9/20; 3,3 sn: 6/12 |
  | **125 Hz** | **20/22** | toplam ~85 sn izlemede 5 dev lif ateşlemesi (3'ü sıçrama) |
  | 100 Hz | 4/8 | 3,3 sn: 0/6 |

- **Karar:**
  - Gövdeli sinek `EMBODIED_VISION` (125 Hz) kullanıyor.
  - Gövdesiz sinek (Fly, Faz 3–4) 250 Hz'de kalıyor.
  - Sinek oturduktan sonra görme açılmadan önce 300 ms yalnızca propriyosepsiyon çalışıyor. Propriyosepsiyonun açıldığı ilk 300 ms'de motor nöronlar ~2 kat ateşliyordu.
- **Açık:**
  - Kalan kendiliğinden kaçışlar (Z-34).
  - Dev lifin yaklaşma sırasındaki zamanlaması literatürle karşılaştırılmadı (Z-25).
  - Instagram kararları gövdeli sinekte yeniden kalibre edilecek (K-020).

## K-030 · Sonraki posta solarak geçiş, koyu tema

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı. K-028'in geçiş kısmının yerine geçti.
- **Bağlam:**
  - K-028'de gerçek kaydırma seçilmiş, sineğin her kaydırmada kaçması "modelin öngörüsü" sayılmıştı (Z-35).
  - Kullanıcı sineğin telefondan korkmasının nasıl önleneceğini sordu: kaçan sinek akışı kaydıramaz.
  - **Kontroller (Z-25):** Kaçış yaklaşmaya özgü değil. Büyümeden kararan bir bölge de, yaklaşan disk kadar kaçış tetikliyor. Gerçek sinekte yaklaşma algılayıcısı LPLC2 kararmaya ve geniş alan kaymasına yanıt vermiyor (Klapoetke ve ark. 2017). Kaydırmadaki kaçış bu yüzden büyük olasılıkla modelin bir eksikliği, öngörüsü değil.
- **Seçenekler:**
  - **Gözü seçici yapmak** (hareket yönü hesabı, yaklaşma algılayıcısı): asıl çözüm, bir araştırma işi.
  - **Ekranı yumuşatmak** (tema ve geçiş biçimi): hızlı ama modelin eksikliğini gizliyor. *Kullanıcı bunu seçti.*
  - **Dopamin:** Denendi, kaçışı önlemiyor (Z-35).
  - **Görme kazancını düşürmek:** 100 Hz'de yaklaşan diske kaçış 4/8'e, 75 Hz'de 0/7'ye iniyor (K-029); sinek tehlikeyi de görmez olur.
- **Ölçüm (125 Hz, her hücrede 12 geçiş; dev lifin ateşlendiği deneme, parantez içinde sıçrama sayısı):**

  | Tema | Kaydırma 400 ms | Kaydırma 250 ms | Anında | Solma 300 ms |
  |---|---|---|---|---|
  | Açık (Instagram varsayılanı) | 12/12 (11) | 8/12 (6) | 1/12 (1) | 1/12 (1) |
  | **Koyu** (Instagram karanlık modu) | 11/12 (11) | 11/12 (7) | 2/12 (1) | **0/12 (0)** |
  | Gri (görsellerin ortalama parlaklığı) | 9/12 (5) | 6/12 (4) | 6/12 (3) | 2/12 (3) |

  - Gri temada 2 postta sinek geçişten önce, beklerken de kaçtı; açık temada 1 postta. Sıçrama sayısı beklemeyi de kapsıyor, bu yüzden gri temada dev lif sayısından büyük çıkabiliyor.
  - 12 deneme az ve sonuçlar ölçümden ölçüme oynuyor. Açık temada anında geçiş önceki ölçümde 5/12, solma 2/12 çıkmıştı. Koyu temada solmanın tekrarında 2/12 çıktı: biri gerçek kaçış (12 spike, sıçrama), öteki tek spike. Aynı tekrarda bir postta sinek beklerken kaçtı.
- **Karar (kullanıcı):**
  - Sonraki posta geçiş **solarak**, 300 ms (`EmbodiedFly.next_post`, `phone.FADE_MS`).
  - Ekran **koyu temada** (`phone.DEFAULT_THEME`).
  - Kaydırma, anında geçiş, açık ve gri tema deneyler için duruyor.
- **Gerekçe:**
  - Solma, açık ve koyu temada en düşük kaçışı veriyor: iki ölçümün toplamında koyu 2/24, açık 3/24.
  - Solmada iki tema arasındaki fark gürültü düzeyinde. Tema kullanıcı tercihi.
- **Ek ölçüm, koyu temanın yan etkisi (kullanıcıya soruldu):**
  - Koyu temada yaklaşan diske tepki zayıflıyor. İki ölçümün toplamında (8 + 16 post, beklerken kaçanlar hariç) kaçış açık temada 22/23 (%96), koyu temada 17/22 (%77). Ortalama LC4 spike'ı açık temada 178–179, koyu temada 68–130.
  - Solma iki temada da düşük kalıyor: 16 postluk tekrarda açık 1/15, koyu 1/14, sıçrama yok.
  - Açık tema önerildi; kullanıcı koyu temada kalmayı seçti.
- **Bedel:**
  - Instagram akışında solarak geçiş yok; gerçekçilik azaldı.
  - Koyu temada yaklaşan nesneye kaçış %96'dan %77'ye iniyor.
  - Faz 8'de gerçek ekran görüntüleri de karanlık modda alınmalı.
- **İlke notu:** Dünya tarafında bir karar; sineğin nöronlarına ve kaçış devresine dokunulmadı. Gözün yaklaşmayı kararmadan ayıramaması (Z-25) açık kalıyor. Korku tepkisinin anlam taşıması gereken Faz 7'de yeniden ele alınmalı.

## K-031 · Düşen sineği deneyci yeniden yerleştirir

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Bağlam:**
  - Gövdeli sinekte kalibrasyon için 6 sinek 80'er posta art arda baktı. Pencerelerin %60'ında sinek dik değildi.
  - **Neden:** Kaçış sıçraması (dev lif → TTMn) sineği ~1,3 mm fırlatıyor ve sinek sırtüstü iniyor. Modelde iniş denetimi ve doğrulma davranışı yok (Z-26, Z-29), bu yüzden sinek ters kalıyor.
  - **Sıklık:** Kendiliğinden kaçışlar ~17 sn'de bir oluyor (Z-34). Uzun bir oturumda neredeyse her sinek bir noktada sırtüstü kalıyor. 6 sinekten yalnızca biri 80 post boyunca dik kaldı; üçü ilk postta ya da ondan önce düştü.
- **Seçenekler:**
  - **Deneyci yeniden yerleştirsin.** *Önerildi, kullanıcı bunu seçti.*
  - **Kaçış oturumu bitirsin:** Çıkış kanalının anlamıyla uyumlu, ama oturumlar birkaç post sürerdi.
  - **Doğrulma davranışını modellemek:** En doğru yol ama büyük bir araştırma işi; yürüme bile henüz yok.
- **Karar:**
  - **Tetik:** Sinek `REPOSITION_MS` (1 sn) boyunca dik değilse deneyci onu oturma sonundaki dik duruşuna geri koyar. "Dik değil": göğüs dikeyi ile dünya dikeyi arasındaki açının kosinüsü `UPRIGHT_MIN`'den küçük (ilk sürümde 0,5; güncelleme aşağıda: 0,9).
  - **Yerleştirme:** Sinek olduğu yerde kalır, yönü telefona çevrilir.
  - **Tutma:** Deneyci sineği `HOLD_MS` (1 sn) boyunca bu duruşta tutar, sonra bırakır. Bu sürede beyin, görme ve propriyosepsiyon çalışır, gövde hareket etmez.
  - **Kayıt:** Her yerleştirme `EmbodiedFly.repositions` ve `Trace.repositions` içinde işaretlidir; görselleştirmede de açıkça gösterilmelidir.
  - Sahne kurulmuşsa varsayılan olarak açık.
- **Neden tutma var:**
  - Tutma olmadan sinek yerleştirildiği anda ters görüntüden telefon görüntüsüne geçiyordu. Görme uyarımı ~195 kHz'e sıçradı ve 40 ms içinde yeni bir kaçış tetiklendi; sinek yine devrildi.
  - Gerçek bir deneyci de sineği bir süre tutarak yerleştirir. Tutma süresinde gözler yeni görüntüye kendiliğinden uyum sağlıyor. Süre görme uyumunun zaman sabitine eşit alındı (VARSAYIM).
- **İlke notu:**
  - Bu bir dünya müdahalesi; sineğin davranışı değil.
  - Kaçış ve düşüş olduğu gibi görünür; müdahale yalnızca sinek sırtüstü kaldıktan sonra gelir.
  - Tutma sırasında dev lif ateşlerse gövde sıçramaz. Bu kaçışlar kayıtta görünür, gövdede görünmez.
- **Güncelleme (2026-09-17, kullanıcı kararı): yatık sinek de yerleştirilir.**
  - **Bulgu:** Homeostaz oturumunda son 50 postta tımar %41'e çıktı. Karar vermeden yapılan uzun gözlemde (3 sinek × 300 sn) nedeni görüldü:
    - Sinek yan yatmış ama devrilmemiş bir duruşa takılıyor: diklik 0,55–0,80, göğüs 0,45 mm'de (dik sinekte 0,65 mm), bacaklar dağınık.
    - Bu duruş 55–80 sn sürdü ve 0,5 eşiğine yakalanmadı. Bu sırada bacaklar dik duruştakinden çok hareket ediyor: ön bacak yolu medyanı sinek 0'da 13°, sinek 2'de 2,3° (dik sinekte 0,5–0,9°). Tımar ve ileri kanalları gövde onayını kolayca geçiyor.
    - Sayaç da her anlık düzelmede sıfırlanıyordu. 0,5 çizgisinin iki yanında sallanan sinek 15 sn boyunca yalnızca bir kez yerleştirildi.
    - Pencerelerin %24'ünde sinek dik değildi. Dik pencerelerde en düşük diklik ≥ 0,98, yatıklarda ≤ 0,80; arada 1800 pencereden yalnızca biri var.
  - **Seçenekler:**
    - **Yerleştirme kuralını sıkılaştırmak.** *Önerildi, kullanıcı bunu seçti.*
    - **Yatık sinek karar vermesin:** Takılma sürer, akış bir dakikayı aşan süreler boyunca durur.
    - **İkisi birden.**
  - **Karar:**
    - `UPRIGHT_MIN` = 0,9 (~25° yatma).
    - Dik olmayan süre sayacı dik anlarda sıfırlanmıyor, yarı hızla azalıyor (`RECOVER_RATE`, `down_time`). Kısa bir sıçrama yatması birkaç yüz ms içinde unutuluyor.
  - **Birlikte bulunan hata:** Oturma beyin çalışırken yapılıyor ve ~40 oturmada bir sinek yatık kalıyor (diklik ~0,38). Bu durumda o duruş "dik duruş" diye kaydediliyor ve deneyci sineği hep ona geri koyuyordu. Artık oturma sonunda sinek dik değilse oturma baştan yapılıyor (`SETTLE_TRIES`).
    - Gövdeli kalibrasyon, doğrulama ve oturumdaki 21 sinek tohumunun hepsi dik oturmuştu; bu ölçümler etkilenmedi.
    - `escape.py` ve `scene.py` sineği denemeler arasında yeniden sıfırlıyor. Oradaki denemelerin ~%2,5'i yatık başlamış olabilir (K-029, K-030 sayıları).
  - **Sonuç (09-govde.md 17.8–17.9):**
    - Kalibrasyonda dik olmayan pencere %9,2'den %7,1'e indi; eşikler yeniden çıkarıldı.
    - Doğrulamada tımar %15,8'den %7,5'e indi.
    - Homeostaz oturumunun son bloğunda tımar %41 yerine %7.
    - Aynı sinek eski kuralda ~60. saniyede yatıp kalıyor, yeni kuralda dik (video).

## K-032 · Gövde onayı: hareket yoksa eylem yok

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı. K-020'nin güvencesini somutlaştırıyor.
- **Bağlam:**
  - K-020'ye göre Instagram eylemleri nöral okumadan seçiliyor, gövde aynı nöronlarla hareket ediyor. Tutarsızlıklar ölçülüp kullanıcıyla çözülecekti.
  - **Ölçüm:** Gövdeli sinekte 480 referans post, eşikler yeniden çıkarıldı. Kararların bir kısmında ilgili gövde bölgesi hiç görünür hareket etmedi (≥ 1° ya da ≥ 0,1 mm; sıçramalı pencerede yalnızca çıkış sayılıyor):

    | Karar | Karar sayısı | Görünür hareketli karar |
    |---|---|---|
    | sonraki post (bacaklar) | 166 | %92 |
    | beğen / kaydet (hortum) | 77 | %96 |
    | yorum (kanatlar) | 10 | %100 |
    | tımar (ön bacaklar) | 24 | %88 |
    | takip et (karın, medyan 0,99°) | 8 | %38 |
    | çıkış (sıçrama) | 9 | %44 |
    | sekme değiştir (baş, medyan 0,24°) | 25 | %0 |
    | önceki post (geri hareket) | 7 | %0 |

  - İlk sayımda (sıçramalı pencerelerde her bölge görünür sayılırken) oranlar daha yüksek çıkmıştı: sonraki post %99, tımar %96, takip %50.

- **Seçenekler:**
  - **Gövde onayı şartı.** *Önerildi, kullanıcı bunu seçti.*
  - **Yalnızca raporlamak.**
  - **Görünmeyen kanalları kapatmak.**
- **Karar:**
  - **Onay şartı:** Bir kanal ancak ilgili gövde bölgesi o 500 ms'lik pencerede görünür biçimde hareket ettiyse karar verebilir. Eşikler: eklemlerde açı yolu ≥ 1°, göğüste ≥ 0,1 mm (VARSAYIM).
  - **Eşikler:** Karar kuralı referans postlara bu şartla uygulanarak çıkarılıyor (`flybrain/motor/calibration_embodied.json`, `body_confirmation: true`).
  - **Sıçrama:** Sinek o pencerede sıçradıysa yalnızca çıkış onaylanır. İlk doğrulamada sekme kararlarının hepsi sıçramalardaydı: baş, gövdeyle birlikte savruluyordu.
  - **Hız şartı:** Hızı sıfır olan kanal karar veremez. Bu kural gövdesiz sinekte de geçerli; onun mevcut eşiklerinde bir şey değiştirmiyor.
  - **Kod:** `flybrain/body/confirm.py`, `flybrain/body/viewer.py` (`FeedViewer.look`).
- **Sonuçlar:**
  - "Önceki post" pratikte hiç olmuyor. Sinek geri yürümüyor; geri kanalı da postların ~%2'sinde ateşliyor.
  - "Sekme değiştir" çok seyrek.
- **Sınırlar:**
  - Onay, bölgenin hareket ettiğini gösterir; hareketin kararı veren nöronlardan geldiğini değil.
  - "Sonraki post" bacak hareketiyle onaylanıyor ama sinek yürümüyor (K-026).
  - İlgi kaybında akış hareket olmadan ilerliyor. Bu bir karar değil, kararın yokluğu; Z-27'de açık kalıyor.


## K-033 · İzleme paneli: kayıttan oynatan tarayıcı paneli ve video

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Bağlam:**
  - Faz 6'nın amacı bir oturumu baştan sona izlenebilir yapmak: 3D sinek, 3D sinir sistemi, sineğin gördüğü, telefon ekranı ve kararlar senkron görünmeli.
  - Görülen her hareket, o anda ateşleyen motor nöronlara kadar geriye izlenebilmeli.
  - **Hız sorunu:** Kapalı döngü gerçek zamanın ~3 katı yavaş (Z-21). Canlı izleme ancak ağır çekim olabilir (Z-28).
- **Seçenekler:**
  - **Tarayıcı paneli ve video.** *Önerildi, kullanıcı bunu seçti.*
  - **Yalnızca video:** İndirme yok ama etkileşim de yok.
  - **Önce video, panel sonra.**
- **Karar:**
  - **Kayıt ile izleme ayrı:** Oturum önce kaydedilir (`flybrain/viz/record.py`), sonra istenen hızda oynatılır.
  - **Gövdenin yeniden kurulması:** Durum vektörü ve telefon ekranının konumu 5 ms'de bir kaydedilir. Gövde bunlardan yeniden kurulur; fizik yeniden çalışmaz.
  - **Spike kaydı:** Spike'lar milisaniye çözünürlüğünde, nöron indeksiyle kaydedilir.
  - **Panel** (`flybrain/viz/web/`, `python -m flybrain.viz.serve <kayıt>`):
    - sinek ve telefon ekranı (3D), sinir sistemi (3D, soma konumları), gözler, telefon, karar günlüğü;
    - zaman çizgisi ve oynatma hızı;
    - geriye izleme: bir karara tıklanınca o kanalın nöronları, bir gövde parçasına tıklanınca o parçayı hareket ettiren kasların motor nöronları.
  - **Video** (`python -m flybrain.viz.video <kayıt>`): Aynı kayıttan paylaşılabilir video üretilir. Hız 1'den küçükse video "ağır çekim" diye etiketlenir.
  - **İndirme (kullanıcı izniyle):** three.js 0.186.0 (MIT), npm'den. Repoya yalnızca üç dosya ve lisansı girdi (`flybrain/viz/web/vendor/`); panel internetsiz çalışır.
- **VARSAYIM:** Somasız nöronların (~%15, çoğu duyu nöronu) konumu, bağlantılı oldukları nöronların konumlarının sinaps sayısıyla ağırlıklı ortalaması. Panelde bu nöronlar ayrı bir seçenekle gizlenebilir.
- **İlke notu:** Görselleştirme yalnızca kaydı gösterir; kayıtta olmayan hiçbir hareket ya da etkinlik çizilmez. Sinek parçalarının rengi MuJoCo dokularının ortalama rengidir.

## K-034 · Faz 8: ekran görüntüsü sineğe, karar gerçek düğmeye

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı (sıradaki adım Faz 8)
- **Bağlam:** Kullanıcı iki şey sordu: gerçek Instagram'da kaydırma sineği yine korkutur mu, ve beğeni/yorum/kaydetme/takip gerçekten Instagram'da nasıl olacak?
- **Karar:**
  - **Sinek tarayıcıyı görmez.** Tarayıcının ekran görüntüsü (telefon görünümü, karanlık mod) sineğin sahnesindeki telefona **solarak** gelir (K-030). Tarayıcı asıl kaydırmayı solma sürerken perde arkasında yapar; sinek kaymayı hiç görmez (Z-35).
  - **Eylemler gerçek düğmelere uygulanır:** beğen, kaydet, takip, yorum. Her eylemden sonra düğmenin durumu yeniden okunur; değişmediyse eylem "başarısız" diye kaydedilir.
  - **Eylemin sonucu sineğe geri gösterilir:** eylem sonrası ekran görüntüsü telefona basılır, yani sinek kalbin kırmızıya döndüğünü görür.
  - **Sıra:** (1) yerel sahte akışta uçtan uca deneme, (2) gerçek hesapta kuru çalıştırma (tıklama yok), (3) düşük limitli gerçek oturum. Her aşama kullanıcı onayıyla.
  - **Giriş kullanıcıya ait:** kalıcı profil `browser-profile/`, kod şifre görmez.
- **Gerekçe:** Sineğin gördüğü ekranla Instagram'ın gerçek durumu tek kaynaktan gelir (ekran görüntüsü), eylemler de aynı sayfada doğrulanır. Böylece "sinek şunu gördü, şunu yaptı" zinciri kayıtla kanıtlanabilir.
- **Riskler:** Z-10 (otomasyon kullanım şartlarına aykırı), Z-36 (arayüz etiketleri değişebilir), Z-37 (video zamanı).
- **Kod:** `flybrain/insta/` (browser, feed, screen, governor, session), `tests/sahte_akis.html`

## K-035 · Story: sineğin kendi oturum videosundan kesit

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Bağlam:** Post paylaşımı Faz 9'da planlıydı (K-004, K-005); **story hiçbir belgede yoktu, atlanmıştı.**
- **Seçenekler:** oturum videosundan kesit / postla aynı görseller (nöral portre, yürüyüş resmi) / ikisi, seçim sinekte
- **Karar:** Oturum videosundan kesit. Faz 6'nın video dışa aktarımı (`viz/video.py`) zaten sineğin gövdesini, beyin aktivitesini ve gördüğü ekranı birlikte çiziyor; bu kayıt olduğu için ilke 6'ya uyuyor.
- **Nasıl paylaşılacak:** Instagram'ın mobil düzeninde story yükleme yolu var; tarayıcı zaten telefon görünümünde çalışıyor (K-006). Resmi API story'ye izin veriyor ama işletme/üretici hesabı ve bağlı Facebook sayfası istiyor; tarayıcı yolu seçildiği için gerekmiyor.
- **Açık:** Story'nin **ne zaman** paylaşılacağı ve videonun hangi anından kesileceği sineğin durumuna bağlanacak; kural Faz 9'da belirlenecek.

## K-036 · Yorum metni: duygu sinekten, kelimeler koklanarak

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı
- **Bağlam:** K-005 yalnızca kendi postunun açıklamasını tanımlıyordu; yorumun metni kararlaştırılmamıştı. Kullanıcı yorumun "sineğin hissettiği şeye, beyninin neresinin yandığına" göre yazılmasını istedi (korku, libido, açlık gibi).
- **Kısıt:** Sinek dil bilmiyor. Kelimeler ya feed'den gelir ya da insanın yazdığı bir tablodan. "Duygu → kelime tablosu" seçilseydi cümleyi insan kurmuş olurdu (ilke 3, K-003).
- **Karar (hibrit):**
  - **Duygu sinekten okunur:** korku (LC4/LPLC2 → dev lif), besleme (şeker yolu → hortum), kur (pC1, şarkı komutu), ödül/ceza (PAM/PPL1), rahatsızlık (tımar kanalı). Okuma, motor okumayla aynı biçimde nöron havuzlarının hızından yapılır; eğitilmiş yorumlayıcı yok.
  - **Kelimeler koklanarak seçilir:** Adaylar sineğin feed'de karşılaştığı kelimeler (K-013 kelime → koku). Koklama, sineğin **o anki beyin durumunda** yapılır; korkmuşken yaklaştığı kelime ile açken yaklaştığı kelime farklı olabilir. Duygu kelimeyi doğrudan vermez, seçimi değiştirir.
  - **Duygunun ayrıca belirledikleri:** yorumun uzunluğu ve sonundaki emoji (küçük, sabit tablo), karar günlüğüne yazılan "baskın duygu".
- **Ön koşul (ölçülecek):** Aynı kelime farklı beyin durumlarında gerçekten farklı yanıt alıyor mu? Fark çıkmazsa duygu yalnızca emojiyi ve uzunluğu belirler; bu durum açıkça raporlanır.
- **Bilinen sınır:** Modelde açlık gibi bir **dürtü** yok; yalnızca şekere verilen anlık yanıt var. Kur devresi (pC1) postlarda neredeyse hiç ateşlemedi (K-017); libido baskın duygu olarak nadiren çıkacak.

## K-037 · Gerçek feed'de geçiş 1200 ms

- **Durum:** kabul edildi (2026-09-17), kullanıcı kararı. K-030'un geçiş süresini gerçek feed için günceller; yerel akışta 300 ms duruyor.
- **Bağlam:** Gerçek Instagram'daki ilk kuru çalıştırmalarda sinek postların yaklaşık üçte birinde "çıkış" (uçup gitme) kararı verdi. Kaçışlar hep geçişin hemen ardındaki ilk pencerede oldu (z = 19–30).
- **Ölçüm** (gerçek feed'den alınmış 9 ekran görüntüsü, 8 ardışık çift; kaçış kararı = çıkış kanalı eşiği aşıyor):

  | Geçiş | Kaçış | Dev lif spike | Sıçrama |
  |---|---|---|---|
  | anında | 5/8 | 155 | 4 |
  | 300 ms (K-030) | 6/8 | 224 | 6 |
  | 600 ms | 4/8 | 151 | 4 |
  | **1200 ms** | **2/8** | 57 | 1 |

- **Karar:** Gerçek feed'de postlar arası geçiş 1200 ms (`insta/session.py`, `REAL_FADE_MS`). Yerel sentetik akışta 300 ms değişmedi; oradaki ölçümler (K-030) o süreyle yapıldı.
- **Gerekçe:** Dünya tarafında bir ayar; sineğin devresine dokunulmuyor. Gerçek fotoğraflar sentetik postlardan çok daha kontrastlı ve K-030'un 300 ms'i bunlara yetmiyor.
- **Bedel:** Instagram'da böyle bir geçiş yok; gerçekçilik azalıyor. Kök neden (gözün yaklaşmayı kontrast değişiminden ayıramaması, Z-25) duruyor ve Faz 7'ye kalıyor.
- **Ek karar (deneyci):** "Çıkış" kararı oturumu bitirmiyor; sinek uçup gidince deneyci onu geri getiriyor ve akış sürüyor (K-031'deki yeniden yerleştirmenin aynısı). Her geri getirme kayda geçiyor.

## K-038 · Telefon dünyada duran bir nesne; mesafeyi sinek seçiyor

- **Durum:** kabul edildi (2026-09-18), kullanıcı kararı. K-030'un sahne düzenini değiştirir.
- **Bağlam:** Kullanıcı canlı yayında gördü: "postun tamamı görüş açısının içinde kalmıyor, büyük oranda sadece alt kısmını görüyor". Ölçüldü — postun üst üçte biri sineğin gözünün yalnızca **%11'ini**, alt üçte biri **%57'sini** kaplıyordu. Sebebi ekranın sineğin **başını izleyen** 180°'lik bir yüzey olmasıydı: bir kask gibi, tepesi 81° yukarıda.
- **İlk deneme ve neden yetmediği:** Ekranı daraltmak kadrajı düzeltiyor (70°'te %37/%37/%26) ama **kaçışı söndürüyor**: yaklaşan disk de küçüldüğü için dev lif ateşlemiyor.

  | Ekran açısı | LC4 | dev lif | Sıçrama | Kaçtı mı |
  |---|---|---|---|---|
  | 180° | 154 | 16 | 3,24 mm | evet |
  | 120° | 15 | 0 | 0,01 mm | hayır |
  | 90° | 13 | 0 | 0,04 mm | hayır |
  | 70° | 3 | 0 | 0,04 mm | hayır |

  "Postun tamamı görünsün" ile "kaçış çalışsın" doğrudan çelişiyor: ikisi de uyaranın gözde kapladığı açıya bağlı, ters yönde.
- **Karar:** Ekran sineği izlemeyi bıraktı; dünyada sabit duran bir nesne (`SceneConfig.follow=False`). Telefonun fiziksel boyu değişmedi (6,3 × 13,6 mm), yalnızca sinek 2,0 mm yerine **2,5 mm** uzakta başlıyor. Mesafeyi bundan sonra sineğin kendi yürüyüşü belirliyor.
- **Ölçüm** (telefonun fiziksel boyu sabit, 3 tohum):

  | Mesafe | ekran gözün | postun üstü/ortası/altı | LC4 | sıçrama | kaçış |
  |---|---|---|---|---|---|
  | 2,0 mm (eski) | %33 | %11,6 / %29,1 / %59,3 | 35 | 2,40 mm | 2/3 |
  | **2,5 mm** | %27 | %12,3 / %38,2 / %49,5 | 48 | 1,32 mm | **2/3** |
  | 3,0 mm | %25 | %14,8 / %42,8 / %42,3 | 64 | 1,49 mm | 1/3 |
  | 4,0 mm | %23 | %21,8 / %45,0 / %33,2 | 22 | 0,10 mm | 0/3 |
  | 5,0 mm | %21 | %29,7 / %42,5 / %27,9 | 16 | 0,10 mm | 0/3 |

- **Gerekçe:** 2,5 mm kaçışı eskisi kadar koruyor (2/3, LC4 daha yüksek) ama postun alt kısmının baskınlığını %59'dan %49'a indiriyor. Asıl kazanç sayıda değil, **mesafenin artık sineğin kararı olmasında**: korktuğunda geri çekiliyor (ölçülen kaçış yer değiştirmesi 1,7–1,9 mm) ve postu daha geniş görüyor; yaklaşırsa bir şeyin üstüne gelmesi onu yeniden kaçırabiliyor. Önceden ekran başına yapışık olduğu için bunların hiçbiri olamıyordu.
- **Bedel:** Bütün kalibrasyonlar (K-016/K-031 motor eşikleri, K-036 duygu ölçeği) 180°'de ölçülmüştü; yeniden ölçüldü. Önceki oturumlarla sayısal karşılaştırma koptu.
- **Bilinen sınır:** Sinek gezinirken pratikte yürümüyor (ölçüm: pencere başına 0,001–0,05 mm), yani mesafeyi asıl değiştiren şey kaçışlar. "Sinek postu incelemek için geri çekiliyor" henüz gözlenmedi; başlangıç mesafesi hâlâ bizim seçtiğimiz bir sayı.
