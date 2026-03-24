# PetShop İmha ve Son Envanter Modülü - Bölüm 6
import sys

from modules.defter import magaza_acilis, sevkiyat_urunu_ekle, urun_imha_et

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    magaza_acilis()

    print("\n--- 📝 GÜN SONU İŞLEMLERİ VE SON ENVANTER ---")

    urun_imha_et(
        "Tüy Dökümü Engelleyici",
        15,
        "SKT Geçtiği İçin İmha Edildi",
    )

    sevkiyat_urunu_ekle("Şeffaf Taşıma Çantası (L)", 10, 350)
    sevkiyat_urunu_ekle("Ahşap Kanarya Folluğu", 25, 45)

    print(
        "\n✅ Kankam, sıralı listemizin sonuna geldik. Dükkan şu an denetime %100 hazır!"
    )
