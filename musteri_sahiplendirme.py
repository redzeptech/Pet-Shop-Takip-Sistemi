"""Müşteri ve sahiplendirme — CLI örneği (defter: database/petshop_defteri.json)."""
import pathlib
import sys

_root = pathlib.Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from modules.defter import magaza_acilis, musteri_kaydet, musteri_sorgula

if __name__ == "__main__":
    magaza_acilis()

    musteri_kaydet(
        ad_soyad="Ahmet Vefa",
        tc_no="12345678901",
        telefon="0555-123-4567",
        adres="Cumhuriyet Mah. Dürüstlük Sok. No:7",
        alinan_canli="Jako Papağanı (Profesör)",
    )

    musteri_sorgula("Ahmet")
