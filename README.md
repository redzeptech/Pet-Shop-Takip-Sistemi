# Pet Shop Takip Sistemi

Bu proje, sabah 07:00'de işe gelip kıymeti bilinmeyen, dürüst bir emeklinin hayalidir.

## Klasör yapısı

| Yol | Açıklama |
|-----|----------|
| `main.py` | Dükkanın ana giriş kapısı — masaüstü uygulamasını başlatır. |
| `database/` | `petshop_defteri.json` dosyasının tutulduğu alan (tüm kalıcı veri). |
| `modules/` | Stok, finans, defter, müşteri vb. Python modülleri. |

## Çalıştırma

Proje kökünde:

```bash
python main.py
```

## Modüller (özet)

- `modules/stok.py` — yem stokları  
- `modules/finans.py` — genel giderler  
- `modules/aksesuar.py` — aksesuar stok / satış  
- `modules/defter.py` — JSON defter, resmi kayıt, sağlık, imha, sevkiyat, müşteri  
- `modules/musteri.py` — sahiplendirme ve hatırlatma API’si (`defter` üzerinden)  
- `modules/mali_rapor.py` — ay sonu mali özet  
- `modules/kus_cenneti.py` — kuş / Jako etkileşimi  

## Veri dosyası

Varsayılan kayıt yolu: `database/petshop_defteri.json`. Bu dosyayı yedekleyerek tüm işletme verisini taşıyabilirsiniz.
