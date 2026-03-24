"""MİZAÇ PetShop — konsol ana menü (GUI olmadan dükkan paneli)."""
import pathlib
import sys

_root = pathlib.Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from modules.defter import (
    SKT_KRITIK_GUN,
    hatirlatmalari_kontrol_et,
    magaza_acilis,
    musteri_kaydet,
    skt_kontrol_metni,
)
from modules.mali_rapor import mali_rapor_metni


def _musteri_kayit_sihirbazi():
    print("\n--- 🐦 Canlı sahiplendirme / müşteri kaydı ---")
    ad_soyad = input("Ad soyad: ").strip()
    if not ad_soyad:
        print("Ad soyad boş olamaz.")
        return
    tc_no = input("TC (opsiyonel): ").strip()
    telefon = input("Telefon: ").strip()
    if not telefon:
        print("Telefon zorunlu.")
        return
    print("Adres (tek satır; bitince Enter):")
    adres = input().strip()
    alinan = input("Alınan canlı (tür / açıklama): ").strip()
    if not alinan:
        print("Alınan canlı bilgisi zorunlu.")
        return
    musteri_kaydet(
        ad_soyad=ad_soyad,
        tc_no=tc_no,
        telefon=telefon,
        adres=adres,
        alinan_canli=alinan,
        canlilar=None,
        yazdir=True,
    )


def _envanter_ozet():
    from modules.aksesuar import aksesuarlar
    from modules.stok import stoklar

    print("\n--- 📦 Yem stokları ---")
    for urun, miktar in stoklar.items():
        print(f"  • {urun}: {miktar}")
    print("\n--- aksesuar (stok / birim fiyat) ---")
    for ad, detay in aksesuarlar.items():
        print(
            f"  • {ad}: stok {detay.get('stok', '')} | "
            f"{detay.get('fiyat', '')} TL"
        )


def _mali_rapor_goster():
    print(mali_rapor_metni())


def _saglik_skt_goster():
    print(skt_kontrol_metni(SKT_KRITIK_GUN))


def ana_menu():
    magaza_acilis()

    while True:
        print("\n" + "🏠" * 5 + " MİZAÇ PETSHOP YÖNETİM PANELİ " + "🏠" * 5)
        print("1. 🐦 Canlı Sahiplendirme (Müşteri Kaydı)")
        print("2. 📦 Envanter ve Stok Durumu")
        print("3. 📉 Mali Rapor (Gelir-Gider)")
        print("4. 🩺 Sağlık ve SKT Denetimi")
        print("5. 🔔 Günlük Hatırlatmalara Bak")
        print("6. 🚪 Dükkanı Kapat (Çıkış)")
        print("-" * 45)

        secim = input("Lütfen işlem numarasını seçin: ").strip()

        if secim == "1":
            _musteri_kayit_sihirbazi()
        elif secim == "2":
            _envanter_ozet()
        elif secim == "3":
            _mali_rapor_goster()
        elif secim == "4":
            _saglik_skt_goster()
        elif secim == "5":
            hatirlatmalari_kontrol_et()
        elif secim == "6":
            print("Dükkan kapandı, huzurlu uykular kankam. Kayıtlar güvende!")
            break
        else:
            print("Geçersiz seçim, liyakatli bir numara gir kankam!")


if __name__ == "__main__":
    try:
        ana_menu()
    except KeyboardInterrupt:
        print("\n\nMenü kapandı (Ctrl+C). Kayıtlar database/petshop_defteri.json üzerinde.")
