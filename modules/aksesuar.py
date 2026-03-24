# PetShop Envanter Yönetimi - Bölüm 2: Aksesuar ve Sarf Malzemeleri
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

AKSESUAR_STOK_UYARI_ESIK = 3

aksesuarlar = {
    "Pirinç Kafes (Büyük)": {"stok": 5, "fiyat": 450},
    "Ahşap Tünek (3'lü set)": {"stok": 12, "fiyat": 85},
    "Gaga Taşı (Mineralli)": {"stok": 25, "fiyat": 30},
    "Akıllı Suluk (Büyük)": {"stok": 15, "fiyat": 65},
    "Jako Oyuncağı (Zekâ geliştirici)": {"stok": 3, "fiyat": 220},
}


def aksesuar_stok_ekle(urun, miktar, yazdir=True):
    """Stok girişi. (başarı, mesaj) döner — GUI için yazdir=False."""
    if urun not in aksesuarlar:
        msg = "❌ HATA: Ürün bulunamadı."
        if yazdir:
            print(msg)
        return False, msg
    aksesuarlar[urun]["stok"] += miktar
    msg = f"📦 STOK GİRİŞİ: {urun} +{miktar} adet eklendi."
    if yazdir:
        print(msg)
    return True, msg


def aksesuar_satis(urun, adet, yazdir=True):
    """Satış. (başarı, tutar_tl, mesaj) döner."""
    if urun not in aksesuarlar:
        msg = f"❌ HATA: {urun} bulunamadı!"
        if yazdir:
            print(msg)
        return False, 0.0, msg
    if aksesuarlar[urun]["stok"] < adet:
        msg = (
            f"❌ HATA: {urun} stokta yeterli değil veya bulunamadı!"
        )
        if yazdir:
            print(msg)
        return False, 0.0, msg
    aksesuarlar[urun]["stok"] -= adet
    birim = aksesuarlar[urun]["fiyat"]
    tutar = adet * birim
    msg = f"💰 AKSESUAR SATIŞI: {adet} adet {urun} satıldı. Tutar: {tutar} TL"
    if yazdir:
        print(msg)
    return True, float(tutar), msg


if __name__ == "__main__":
    print("\n--- 🎡 AKSESUAR VE SARF MALZEMESİ TAKİBİ ---")
    aksesuar_stok_ekle("Gaga Taşı (Mineralli)", 10)
    aksesuar_satis("Pirinç Kafes (Büyük)", 1)
