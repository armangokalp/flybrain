# 01 — Vizyon ve İlkeler

## Vizyon

Bir sineğe Instagram hesabı verip ne yaptığını izlemek istiyoruz: neye bakıyor, neyi beğeniyor, kimi takip ediyor, ne paylaşıyor? Instagram'ın öneri algoritması da zamanla bu sineğe göre şekillenecek. Proje iki öğrenen sistemin karşılaşmasını gözlemlemeye dayanıyor: bir böcek beyni ve bir sosyal medya algoritması.

## Neden "gerçekten sinek karar veriyor" iddiası önemli?

Konnektom yayınlandıktan sonra Minecraft, DOOM ve Beat Saber oynayan, hatta borsada işlem yapan "sinek beyni" demoları çıktı. Bunların çoğunda konnektomun karmaşık çıktısını ayrıca **eğitilmiş bir yapay zekâ** yorumluyor. Bu durumda asıl kararı sinek değil o yapay zekâ vermiş oluyor.

Aynı sorun sanal gövdeli demolarda da var. Mart 2026'da "sinek beyni sanal bir gövdeyi yürüttü" diye yayılan demoda beyinden yalnızca birkaç inen nöron okunuyordu. Bu nöronlar, gerçek sinek videolarını taklit etmek üzere eğitilmiş hazır hareket programlarını tetikliyordu. Yani görünen hareketi beyin değil, eğitilmiş kontrolcü üretiyordu.

Bu proje o yola girmiyor. Aşağıdaki ilkeler bunu garanti etmek için var.

## İlkeler

1. **Eylemleri sinek seçer.** Her Instagram eylemi, simüle edilen nöronların ateşleme aktivitesinden **sabit ve deterministik** bir okuma kuralıyla çıkar.
2. **Eğitilmiş yorumlayıcı kullanılmaz.** Sinir aktivitesini eyleme çeviren katman hiçbir veriyle eğitilmez. Bu katman, hangi nöron havuzunun hangi davranışı ürettiğini bilen elle yazılmış bir tablodan ibarettir ve tablo nörobilim literatürüne dayanır.
3. **Dil modeli kullanılmaz.** Caption'lar ve yorumlar dahil hiçbir metni bir dil modeli yazmaz.
4. **Rastgeleliğin tek kaynağı biyolojidir.** Duyusal girdiler Poisson süreçleriyle spike'a çevrilir (gerçek nöronlardaki gürültünün modeli). Tohum (seed) değerleri kaydedilir, böylece her karar birebir yeniden üretilebilir.
5. **Her karar gerekçelendirilir.** Her eylem için hangi nöron havuzunun kaç Hz ateşlediği ve eşiğin ne olduğu loglanır. "Sinek bunu neden beğendi?" sorusu her zaman cevaplanabilir olmalı.
6. **Görünen her hareket nöronlardan gelir.** Sineğin 3D gövdesi yalnızca simüle edilen motor nöronlarla hareket eder (motor nöron → kas → eklem → fizik). Animasyon, senaryolu hareket, hazır ritim üreteci ya da eğitilmiş kontrolcü kullanılmaz. Hareket kusurluysa kusurlu gösterilir. Kayıttan oynatma serbesttir, çünkü animasyon değil, simülasyonun kendisinin kaydıdır (K-019).
7. **İnsan müdahalesi sınırlı ve kayıtlıdır.** İnsan yalnızca aşağıdaki "dünyanın fiziği" kategorisinde devreye girer ve yaptığı her şey [kararlar.md](kararlar.md) dosyasına yazılır.

## Kim neyi kontrol ediyor?

### Sinek (simüle edilmiş beyin)

- Bir posta ne kadar süre bakılacağı
- Kaydırma yönü (ileri/geri)
- Beğenme, kaydetme, yorum yapma
- Takip etme ve takipten çıkma
- Oturumu erken bitirme ("uçup gitme")
- 3D gövdenin her hareketi: yürüme, baş çevirme, hortum uzatma, kanat açma, sıçrama
- Post görselinin içeriği
- Caption'da hangi kelimelerin hangi sırayla kullanılacağı
- Ne zaman paylaşım yapılacağı

### İnsan (yalnızca kurulum ve sınırlar)

| Müdahale | Neden gerekli | Sineğin kararını etkiliyor mu? |
|---|---|---|
| Hesabı açmak, ilk birkaç hesabı takip etmek | Sineğe başlangıç feed'i vermek | Başlangıç koşulunu belirliyor, kararları değil |
| Duyu kodlayıcıları ve motor eşleme tablosunu tasarlamak | Sineğin dünyayla bağlantısını kurmak | Evet; bu yüzden tablo sabit, anatomik ve belgeli |
| Motor nöron → kas → eklem tablosu ve kas modeli | Sineğin nöronlarını 3D gövdeye bağlamak | Hareketin biçimini fizik ve anatomi belirler; tablo literatüre dayanır, davranışa bakılarak ayarlanmaz (K-019) |
| Sanal dünya: zemin, Instagram ekranı ve ekranın sineği izlemesi | Sineğe bir çevre vermek | Hayır; yalnızca sineğin gördüğü ve üzerinde yürüdüğü dünyayı tanımlar (K-021) |
| Kalibrasyon (eşikler) | Kas kanallarının tipik yanıt düzeyini ölçmek | Gri ekran ve **içerikten bağımsız referans postlar** (rastgele doku + rastgele kelimeler) ile yapılır; belirli içeriğe karşı istenen davranışa göre asla ayarlanmaz (K-016) |
| Eylem bütçesi (genel sıklıklar: ör. beğeni %15, yorum %2) | Hesabın doğal ve güvenli davranması | Genel sıklığı belirler; **hangi postta** ne yapılacağını sinek seçer (K-016) |
| Güvenlik valisi (hız sınırları, içerik vetosu) | Hesabın banlanmasını ve uygunsuz içeriği önlemek | Yalnızca **veto eder**, kendi başına hiçbir eylem seçmez |
| Instagram güvenlik doğrulamasını (challenge/CAPTCHA) çözmek | Otomasyon bunu yapamaz ve yapmamalı | Hayır; sistem bekler, insan çözer |

## Neyin başarı sayılacağı

- Sinek, gri ekrana karşı sessiz, gerçek görsellere karşı ise ayırt edici tepkiler veriyor.
- Aynı post iki kez gösterildiğinde benzer (birebir aynı olması gerekmiyor) tepkiler çıkıyor.
- Haftalar içinde feed'in içeriği sineğin davranışına bağlı olarak ölçülebilir biçimde değişiyor.
- Her eylemin gerekçesi loglardan geriye doğru izlenebiliyor.
- 3D gövdede görülen hareketler ile Instagram'da yapılan eylemler örtüşüyor (K-020) ve beyin aktivitesiyle birlikte izlenebiliyor.
