# PetShop Sağlık Envanteri - Bölüm 5: Vitamin ve Kuş Kumları (SKT Takipli)
import sys

from modules.defter import magaza_acilis, saglik_urunu_ekle, skt_kontrol_et

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    magaza_acilis()

    saglik_urunu_ekle("B-Vitamini Kompleksi", 10, "2024-12-31")
    saglik_urunu_ekle("Kalsiyum Destekli Kum", 20, "2024-04-15")
    saglik_urunu_ekle("Tüy Dökümü Engelleyici", 15, "2023-10-01")

    skt_kontrol_et()
