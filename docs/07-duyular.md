# 07 — Duyu Kodlayıcıları (Faz 3)

> 2026-09-16. Kod: [`flybrain/senses/`](../flybrain/senses/). Deneyler: [`flybrain/experiments/vision.py`](../flybrain/experiments/vision.py), [`flybrain/experiments/post.py`](../flybrain/experiments/post.py)

Bir Instagram postu sineğe üç kanaldan ulaşıyor:

| Instagram | Sinek duyusu | Modül | Hedef nöronlar |
|---|---|---|---|
| Görsel | Görme | `vision.py` + `eye.py` | ON/OFF yolunun ilk uyarıcı nöronları (L2, L3, Mi1, Tm3); yaklaşık 7.400 nöron |
| Caption, hashtag, emoji | Koku | `olfaction.py` | 53 glomerül tipinde 2.635 koku alıcı nöron |
| Beğeni, yorum, takipçi | Ödül / ceza | `reward.py` | PAM (316) / PPL1 (16) dopamin nöronları |

Kodlayıcıların hepsi ortak bir `Stimulus` (nöron → Poisson hızı) yapısı üretiyor; uyarımlar toplanabiliyor.

---

## Koku: kelime → koku molekülü (K-013)

- **Ayrıştırma:** metin küçük harfe çevrilir; kelimeler ve emojiler ayrılır, noktalama ve `#` atılır.
  - Örnek: `"Merhaba DÜNYA! #kahve ☕️ İstanbul"` → `merhaba, dünya, kahve, ☕, istanbul`
- **Kelime → glomerüller:** kelime her glomerül adıyla birlikte özetlenir (blake2b); en küçük özete sahip **3 glomerül** seçilir.
  - Eşleme sabittir: aynı kelime her zaman aynı kokuyu verir.
  - Rastgelelik ya da anlam içermez.
  - Yeni glomerül eklense bile mevcut eşlemeler büyük ölçüde korunur.
- **Metin → karışım:** bir glomerülün etkinliği, onu seçen kelime sayısıdır. Hız reseptör doygunluğu gibi artar: `200 Hz · a / (a + 1/3)`.
  - Tek kelime 150 Hz verir; bu, Faz 2 deneyleriyle aynı yoğunluk.
  - Aynı glomerülü seçen üç kelime 180 Hz verir.
- İlk 40 kelime kullanılır.

## Ödül ve ceza

- Kendi postlarına gelen beğeni ve yorumlar ile yeni takipçiler PAM nöronlarını uyarır.
- Takipçi kaybı PPL1 nöronlarını uyarır.
- Hız: `150 Hz · n / (n + 5)`. Öğrenme kuralı Faz 10'da eklenecek.

---

## Göz geometrisi

Görseli doğru kolona vermek için, MaleCNS'nin kolon koordinatlarından (`hex1`, `hex2`) gerçek göz geometrisi çıkarıldı.

### Izgara

- Fiziksel olarak en yakın 6 komşu (±1,0), (0,±1) ve ±(1,1) adımlarında. Diğer köşegen (+1,−1) daha seyrek (27'ye karşı 45).
- Bu, eksenleri arasında 120° olan bir altıgen ızgara demek: `x = hex1 − hex2/2`, `y = hex2·√3/2`.

### Bakış yönleri

1. Beyin eksenleri, bilinen noktalardan çıkarıldı:
   - **ön:** koku lobu projeksiyon nöronlarının gövdeleri − Kenyon hücrelerinin gövdeleri
   - **sırt:** Kenyon hücreleri − SEZ motor nöronları
2. Sağ gözün 550 lamina hücre gövdesine bir küre oturtuldu (yarıçap 134 µm). Her kolonun bakış yönü, kürenin o noktadaki dış normali olarak alındı.
3. Izgaradan bakış yönüne doğrusal bir eşleme kuruldu:
   - yatay açı φ için R² = 0,75, yükseklik θ için R² = 0,93
   - kapsam: φ −17° (yan-arka) ile 95° (tam ön) arası, θ −64° ile 75° arası
   - komşu kolonlar arası yaklaşık 3–4°, sinek gözü için bilinen ~5° değerine yakın
4. **Doğrulama:** gözün üst kenarındaki (dorsal rim) R7d/R8d fotoreseptörleri +57° yükseklikte çıktı; beklendiği gibi "yukarıda".
5. **Sol göz:** hücre gövdesi verisi eksik; küre oturtma bozuk sonuç verdi (φ 189°'ye kadar). Üst kenar fotoreseptörlerinin iki gözde de aynı kolonlarda (h1 ≈ 30, h2 ≈ 35) olması, iki gözün ayna simetrik koordinatlar kullandığını gösteriyor. Bu yüzden sağ gözün eşlemesi iki göze de uygulanıyor.

### Koordinatı olmayan nöronlar

Kolonları, koordinatlı partnerlerinin sinaps ağırlıklı oylamasıyla bulunuyor. İkinci turda, kolonu yeni çıkarılan partnerler de oy veriyor; örneğin R7'ler aynı ommatidyumdaki R8 üzerinden.

| Grup | Kolon atanan |
|---|---|
| L2 + L3 | 3.549 / 3.551 |
| Mi1 + Tm3 | 3.827 / 3.827 |
| R1–R6 | 1.389 / 1.394 |
| R7 | 1.291 / 1.299 (ikinci tur olmadan %47) |
| R8p / R8y | 329 / 330, 981 / 999 |

### Panoramik gösterim (K-014)

Post görseli sineğin tüm görme alanına yayılıyor:

- Görselin sol yarısı sol göze, sağ yarısı sağ göze düşüyor.
- Görselin ortası tam önü, kenarları gözlerin en arka kolonlarını gösteriyor; üst kenar sırt yönü.
- Doğrulama: sol yarısı karanlık bir görselde uyarılan OFF nöronlarının 1.764'ü sol, 2'si sağ gözde.

---

## Görme: hangi giriş? (Z-02, K-012)

Görsel, sinek gözü gibi **kontrast** olarak kodlanıyor: `c = (I − Ī) / Ī`.

- Gri ekranda kontrast sıfır, yani "off" ve "onoff" yöntemleri hiç uyarım üretmiyor.
- Sinekler kırmızıyı neredeyse göremediği için parlaklık kanalı R 0,05, G 0,55, B 0,40 ağırlıklarıyla hesaplanıyor.

Üç yöntem karşılaştırıldı:

| Yöntem | Nasıl |
|---|---|
| **off** | Karanlık bölgeler L2 ve L3'ü sürer (OFF yolu, uyarıcı) |
| **onoff** | off + parlak bölgeler Mi1 ve Tm3'ü sürer (ON yolu, uyarıcı) |
| **foto** | Işık fotoreseptörleri sürer. L1–L3, Mi1 ve Tm3 ışıkta sürekli aktifliği taklit eden tonik akım alır, fotoreseptörler de onları ketler (biyolojiye en yakın yöntem) |

Protokol: gri 300 ms → görsel 500 ms → gri 300 ms → gri 200 ms (dönüş ölçümü). 8 sentetik görsel × 3 deneme; beyin ayarı `BRAIN_PARAMS`.

Tablo sütunları:
- **+OL, +VPN, +merkezi, +inen, +motor:** görsel sırasında gri tabana göre 2 Hz'den fazla artan nöron sayısı. Sırasıyla optik lob, görme projeksiyon nöronları, merkezi beyin, inen nöronlar ve motor nöronlar.
- **dönüş:** görselden sonraki aktif nöron sayısının gri tabana göre farkı.

### 1. deneme: kodlayıcının sürdüğü nöronlar da sinaptik depresyona tabi

| yöntem | doğruluk 200 / 500 ms | +OL | +VPN | +merkezi | +inen | gri taban aktif |
|---|---|---|---|---|---|---|
| off 50 Hz | %12 / %12 | 1.597 | 0 | 0 | 0 | 0 |
| off 150 Hz | %12 / %12 | 1.810 | 0 | 0 | 0 | 0 |
| onoff 50 Hz | %71 / %71 | 4.326 | 13 | 154 | 8 | 0 |
| onoff 150 Hz | %54 / %54 | 4.712 | 21 | 212 | 9 | 0 |
| foto 50 Hz, 9 mV | %12 / %12 | 5.739 | 1 | 0 | 0 | 14.368 |
| foto 20 Hz, 12 mV | %12 / %12 | 5.663 | 0 | 0 | 0 | 15.848 |

**Teşhis:** Sinyal optik lobdan çıkamıyor. Kodlayıcının 50–150 Hz'de sürdüğü L2/Mi1 gibi nöronların sinapsları, K-011'deki depresyonla yaklaşık 10 kat yoruluyor. Duyu nöronlarını muaf tutmamızın gerekçesi (Poisson hızı zaten etkin çıktıdır) bu nöronlar için de geçerli. Bu yüzden `Simulator(std_exempt=...)` eklendi ve kodlayıcının sürdüğü nöronlar muaf tutuldu (K-011 eki).

### 2. deneme: kodlayıcının sürdüğü nöronlar muaf

| yöntem | doğruluk 200 / 500 ms | +OL | +VPN | +merkezi | +inen | +motor | gri taban aktif | dönüş |
|---|---|---|---|---|---|---|---|---|
| off 50 Hz | %12 / %12 | 3.654 | 0 | 0 | 0 | 0 | 0 | 0 |
| off 150 Hz | %46 / %54 | 6.537 | 3 | 1 | 1 | 0 | 0 | 0 |
| onoff 50 Hz | %42 / %42 | 6.834 | 65 | 166 | 8 | 1 | 0 | 0 |
| **onoff 150 Hz** | **%75 / %88** | 13.305 | 346 | 407 | 34 | 20 | **0** | **0** |
| foto 50 Hz, 9 mV | %12 / %12 | 6.866 | 40 | 0 | 0 | 0 | 14.896 | +12 |
| foto 20 Hz, 12 mV | %17 / %17 | 9.659 | 111 | 0 | 0 | 0 | 17.185 | −286 |

**Sonuçlar:**
- **ON yolu olmadan sinyal merkezi beyne ulaşmıyor.** OFF yolu tek başına optik lobda kalıyor.
- **foto yöntemi başarısız.** Tonik aktivite gri ekranda bile yaklaşık 15 bin nöronu sürekli ateşletiyor, görsel sinyal ise merkezi beyne hiç ulaşmıyor.
- Sol ve sağ koyu daire, dönme nöronlarında (DNa02) belirgin bir asimetri yaratmadı (en fazla 1 Hz). Sabit görüntüler dönme davranışını tetiklemiyor; gerçek sinekte de dönme büyük ölçüde hareketle tetikleniyor (Z-18).

### 3. deneme: doğal görüntü istatistiği, onoff hız taraması

16 renkli "1/f" gürültü görseli (doğal fotoğrafların genlik spektrumu), 4 deneme; şans düzeyi %6.

| yöntem | doğruluk 200 / 500 ms | +OL | +VPN | +merkezi | +inen | +motor | gri taban | dönüş |
|---|---|---|---|---|---|---|---|---|
| onoff 100 Hz | %45 / %39 | 6.147 | 61 | 99 | 8 | 1 | 0 | 0 |
| onoff 150 Hz | %47 / %53 | 8.063 | 134 | 221 | 14 | 3 | 0 | 0 |
| **onoff 250 Hz** | **%95 / %100** | 11.311 | 278 | 380 | 25 | 14 | **0** | **0** |

**Karar (K-012):** onoff, 250 Hz. Kodlayıcının sürdüğü nöronlar depresyondan muaf.

Yeniden üretmek için:

```bash
python -m flybrain.experiments.vision --set yontemler --images sentetik --workers 6 --trials 3
python -m flybrain.experiments.vision --set onoff-hiz --images dogal --workers 3 --trials 4
```

---

## Birleşik test: görsel + caption

4 doğal görsel × 4 caption = 16 post, 3 deneme. Okuma, inen nöronlarla yapıldı.

Captionlar:
- `sabah kahvesi ☕ #pazartesi`
- `deniz güneş tatil 🌊`
- `kedim yine uyuyor 😴`
- `koşu antrenmanı bitti #spor`

| ölçüt | sonuç | şans |
|---|---|---|
| görsel doğruluğu | **%100** | %25 |
| caption doğruluğu | **%52** | %25 |
| post doğruluğu (görsel + caption) | **%85** | %6 |
| post sırasında aktif nöron (ortalama) | 16.882 (beynin yaklaşık %10'u) | |
| post sonrası kalıcı nöron (en çok) | **0** | |

- Görsel sinyali baskın, ancak caption bilgisi açıkça taşınıyor. Caption hiçbir bilgi taşımasaydı post doğruluğu en fazla %25 olabilirdi.
- Faz 2'de %10 aktivite şüpheliydi, çünkü girdiden bağımsızdı ve kapanmıyordu. Burada aynı oran **girdiye özgü** ve uyarım bitince **tamamen sönüyor**.

Yeniden üretmek için: `python -m flybrain.experiments.post --trials 3`
