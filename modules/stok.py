# PetShop Envanter Yönetimi - Bölüm 1: Yem Stokları
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

stoklar = {
    "Muhabbet Kuşu Yemi (kg)": 10.5,
    "Jako Özel Karışım (kg)": 5.0,
    "Kanarya Melodisi Yemi (kg)": 7.2,
    "Kuş Kumu (paket)": 15,
    "Gaga Taşı (adet)": 20,
}

STOCK_UYARI_ESIK = 3


def stok_durumu_goster():
    print("\n--- 📦 GÜNCEL STOK DURUMU (07:00 Kontrolü) ---")
    for urun, miktar in stoklar.items():
        uyari = "⚠️ STOK AZALIYOR!" if miktar < STOCK_UYARI_ESIK else "✅ TAMAM"
        print(f"{urun.ljust(30)}: {miktar} {uyari}")
    print("-" * 45)


def satis_yap(urun_adi, miktar):
    """Satış yapar. (başarı_mı, mesaj) döner — GUI ve konsol için."""
    if urun_adi not in stoklar:
        return False, "❌ HATA: Ürün bulunamadı."
    if stoklar[urun_adi] < miktar:
        return (
            False,
            f"❌ HATA: Yetersiz stok! Elimizde sadece {stoklar[urun_adi]} var.",
        )
    stoklar[urun_adi] -= miktar
    kalan = stoklar[urun_adi]
    return (
        True,
        f"💰 SATIŞ: {miktar} birim {urun_adi} satıldı. Kalan: {kalan}",
    )


if __name__ == "__main__":
    stok_durumu_goster()

    ok, mesaj = satis_yap("Jako Özel Karışım (kg)", 2.5)
    print(mesaj)

    stok_durumu_goster()
