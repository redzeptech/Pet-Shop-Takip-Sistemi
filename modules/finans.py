# PetShop Finans ve Sağlık Takip Modülü
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

giderler = []

GIDER_UYARI_ESIK = 5000.0


def gider_ekle(kalem, miktar, aciklama, yazdir=True):
    kayit = {
        "kalem": (kalem or "").strip(),
        "miktar": float(miktar),
        "not": (aciklama or "").strip(),
    }
    giderler.append(kayit)
    if yazdir:
        print(
            f"📉 GİDER KAYDEDİLDİ: {kayit['kalem']} - {kayit['miktar']} TL ({kayit['not']})"
        )
    return kayit


def toplam_gider_hesapla(yazdir=True):
    toplam = sum(item["miktar"] for item in giderler)
    if yazdir:
        print(f"\n💸 TOPLAM GİDER: {toplam} TL")
        if toplam > GIDER_UYARI_ESIK:
            print("⚠️ DİKKAT: Giderler artıyor, kombiyi kapalı tutmaya devam kankam!")
    return toplam


if __name__ == "__main__":
    print("\n--- 🏦 RESMİ VE SAĞLIK GİDERLERİ TAKİBİ ---")

    gider_ekle("Belediye Harcı", 1250.00, "Yıllık işletme ve hijyen harcı")

    gider_ekle(
        "Veteriner Kontrolü",
        2500.00,
        "Jako ve kanaryaların periyodik aşı ve parazit uygulaması",
    )

    gider_ekle("Vergi Ödemesi", 3100.00, "Aylık muhtasar ve KDV ödemesi")

    toplam_gider_hesapla()
