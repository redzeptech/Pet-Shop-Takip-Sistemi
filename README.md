# 🐾 Pet-Shop-Takip-Sistemi v2.0
## Ticari Kaygıların Ötesinde, Canlı Onuruna Saygılı İşletme Yönetimi

## 🚩 Vizyon ve Etik Beyanname
Bu yazılım, hayvanların birer "ticari meta" veya "oyuncak" olarak görülmesine karşı bir duruş sergiler.

- 🚫 **Canlı Satışına Hayır:** Sistem, kedi ve köpek gibi memeli canlıların para karşılığı satılmasını reddeder. Teknik altyapı, bu tür bir ticari işlemi desteklemeyecek şekilde kurgulanmıştır.
- 🛡️ **Koruma ve Gözetme:** Hayvanlar çocukların eğleneceği cansız objeler değildir. Yazılımımız, "Sahiplen, Satın Alma" kültürünü destekleyen bir veri yapısına sahiptir.
- ⚖️ **Hukuki Çerçeve:** 5199 sayılı Hayvanları Koruma Kanunu ve uluslararası etik standartlar baz alınmıştır.

## 🛠️ Teknik Özellikler
Proje, bir işletmenin tüm operasyonel ihtiyacını modern bir mimariyle karşılar:

- 📊 **Profesyonel Dashboard:** CustomTkinter ile geliştirilmiş, karanlık mod destekli kurumsal arayüz.
- 🔗 **İlişkisel Veritabanı:** Müşteriler ve evcil hayvanlar arasındaki bağı koparmayan SQLite mimarisi.
- 🚨 **Akıllı Stok Radarı:** Ürünler kritik seviyeye (Örn: <5) düştüğünde otomatik görsel uyarı sistemi.
- 💰 **Finansal Raporlama:** Hizmet bedellerini (Bakım, Traş, Konaklama) ve Ürün satışlarını ayrı kalemlerde takip eden kasa modülü.

## 📂 Proje Yapısı
```text
├── main.py             # Uygulama giriş noktası
├── gui.py              # Modern kullanıcı arayüzü (CustomTkinter)
├── database/           # Kalıcı veri dosyaları
├── modules/            # İş kuralları ve modüller
├── database_manager.py # SQL sorguları ve veri güvenliği
└── docs/               # Etik beyanname ve hukuki metinler
```

## 🚀 İşleyiş ve Kullanım
- **Müşteri Kaydı:** Hayvan sahibinin ve can dostunun bilgilerini sisteme işleyin.
- **Hizmet Yönetimi:** Verilen bakım hizmetlerini (tıbbi olmayan) kasaya aktarın.
- **Stok Takibi:** Ürün girişlerini yapın, sistem azalan ürünler için sizi uyarsın.
- **Raporlama:** Günlük ve aylık gelir-gider tablonuzla işletmenizin sağlığını ölçün.

## 💡 Gelecek Perspektifi (Roadmap)
- [ ] QR Kod Entegrasyonu: Her hayvan için dijital kimlik kartı üretimi.
- [ ] Kara Liste: Hayvana kötü muamele eden kişilerin merkezi takibi.
- [ ] Mobil Bildirim: Mama ve bakım zamanları için otomatik hatırlatıcılar.

## 📜 Lisans ve Kullanım Şartı
Bu yazılımı kullanan her birey/işletme, hayvan haklarına saygılı olacağını ve canlı ticaretinden uzak duracağını taahhüt etmiş sayılır.

## ⚡ Hızlı Başlangıç
Proje kökünde aşağıdaki adımları çalıştırın:

Önce (gerekirse) bağımlılıkları kurun:

```bash
pip install -r requirements.txt
```

Ardından modern arayüzü başlatın:

```bash
python gui.py
```

Klasik arayüz için:

```bash
python main.py
```
