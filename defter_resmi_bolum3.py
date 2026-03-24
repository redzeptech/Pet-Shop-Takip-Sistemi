# PetShop Resmi Defter - Bölüm 3: Belediye, Veteriner ve Vergi Kayıtları
import sys

from modules.defter import magaza_acilis, resmi_gider_isle

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    magaza_acilis()

    resmi_gider_isle("Belediye Ruhsat Harcı", 1500, "BEL-2024-001")
    resmi_gider_isle("Veteriner Sağlık Onayı", 850, "VET-KARNE-JAKO")
    resmi_gider_isle("KDV Ödemesi", 2200, "MAL-TAH-2024")

    print(
        "\nKankam, şimdi arkana yaslan. Müfettiş gelse 'Dosya nerede?' dese, "
        "'database/petshop_defteri.json kankam' dersin!"
    )
