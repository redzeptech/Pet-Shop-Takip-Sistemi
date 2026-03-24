# PetShop Envanter Yönetimi - Bölüm 4: Sarf Malzeme ve Demirbaşlar
import sys

from modules.defter import magaza_acilis, sarf_envanter_dokumu, sarf_malzeme_ekle

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    magaza_acilis()

    print("\n--- 🦴 SARF MALZEME VE DEMİRBAŞ KAYDI ---")

    # 3. Madde: Gaga Taşları ve Kalamar Kemikleri
    sarf_malzeme_ekle("Kalamar Kemiği (Büyük)", 30, 15.0)
    sarf_malzeme_ekle("Gaga Taşı (Mineralli)", 50, 20.0)

    # 4. Madde: Suluk ve Yemlik Yedekleri (Bunlar demirbaştır, kolay bitmez)
    sarf_malzeme_ekle("Otomatik Suluk (Şeffaf)", 20, 45.0)
    sarf_malzeme_ekle("Akıllı Yemlik (Dökülmez)", 15, 75.0)

    sarf_envanter_dokumu()
