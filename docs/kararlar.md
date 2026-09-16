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
- **Karar:** İlk ikisinin karışımı. İkisi de %100 sinek üretimi. Bir postta hangisinin kullanılacağını da sineğin o anki nöral durumu belirler (kural Faz 7'de kesinleşecek).
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

- **Durum:** önerildi (2026-09-16), kullanıcı kararı bekleniyor
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
- **Yeniden değerlendirme:** Faz 3'te görme sinyali ölçüldüğünde bu karar tekrar gözden geçirilecek.
