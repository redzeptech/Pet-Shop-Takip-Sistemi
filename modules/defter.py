# 1. DOSYA KAYIT SİSTEMİ (Maliye ve Belediye Dostu)
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

DOSYA_ADI = "petshop_defteri.json"

# Dosyadan okunan canlı durumu; PetShopApp oluşturulunca uygulanır
PENDING_CANLILAR = None

# Bölüm 3: Belediye, veteriner, vergi — evrak numaralı resmi kayıtlar
resmi_giderler = []

# Bölüm 4: Sarf malzeme ve demirbaş (adet + birim fiyat TL)
sarf_malzemeler = {}

# Bölüm 5: Vitamin, kuş kumu vb. — SKT takibi (YYYY-MM-DD)
saglik_urunleri = {}
SKT_KRITIK_GUN = 30

# Bölüm 6: İmha tutanağı + sevkiyat / son envanter (taşıma, folluk vb.)
imha_kayitlari = []
sevkiyat_urunleri = {}

# Müşteri ve sahiplendirme kayıtları
musteriler = []

# (anahtar kelime, yem günü, aşı günü) — metin ASCII’ye indirgenir (ğ→g, ş→s …)
CANLI_BAKIM_PERIYOTLARI = (
    ("papagan", 30, 60),
    ("jako", 30, 60),
    ("muhabbet", 25, 60),
    ("kanarya", 25, 60),
    ("kus", 28, 60),
    ("kedi", 30, 60),
    ("kopek", 30, 60),
    ("balik", 14, 90),
    ("japon", 14, 90),
    ("hamster", 30, 60),
)
DEFAULT_YEM_GUN = 30
DEFAULT_ASI_GUN = 60


def _alinan_canli_ascii(s: str) -> str:
    s = (s or "").lower()
    tr = str.maketrans("ığüşöçİĞÜŞÖÇ", "igusocigusoc")
    return s.translate(tr)


def periyotlari_al(alinan_canli: str) -> tuple[int, int]:
    """Türe göre (yem gün, aşı gün); eşleşmezse 30 / 60."""
    s = _alinan_canli_ascii(alinan_canli)
    for anahtar, yem_g, asi_g in CANLI_BAKIM_PERIYOTLARI:
        if anahtar in s:
            return (yem_g, asi_g)
    return (DEFAULT_YEM_GUN, DEFAULT_ASI_GUN)


def _islem_tarihi_parse(ham: str):
    if not ham or not str(ham).strip():
        return None
    ham = str(ham).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(ham, fmt)
        except ValueError:
            continue
    return None


def hatirlatma_metni(veri=None) -> str:
    """
    Bugün aranması gereken yem / aşı takipleri (müşteri listesinden).
    veri None ise dosyadan okunur (bellek senkron değilse güvenilir).
    """
    if veri is None:
        veri = defteri_yukle()
    bugun = datetime.now()
    bugun_d = bugun.date()
    satirlar = [
        "🔔" * 5 + " HATIRLATMA — GÜNLÜK BAKIM VE AŞI " + "🔔" * 5,
        f"📅 Bugünün tarihi: {bugun.strftime('%d.%m.%Y')}",
        "-" * 55,
    ]
    herhangi = False
    for musteri in veri.get("musteriler", []):
        islem = _islem_tarihi_parse(musteri.get("islem_tarihi", ""))
        if islem is None:
            continue
        alinan = musteri.get("alinan_canli", "") or ""
        yem_g, asi_g = periyotlari_al(alinan)
        yem_tarihi = (islem + timedelta(days=yem_g)).date()
        asi_tarihi = (islem + timedelta(days=asi_g)).date()
        ad = musteri.get("ad_soyad", "")
        tel = musteri.get("telefon", "")

        if asi_tarihi <= (bugun + timedelta(days=7)).date():
            satirlar.append(
                f"💉 AŞI VAKTİ: {ad} — {alinan}\n"
                f"   📞 {tel} | Randevu / kontrol: {asi_tarihi.strftime('%d.%m.%Y')}"
            )
            herhangi = True

        if yem_tarihi <= bugun_d:
            satirlar.append(
                f"🍴 YEM KONTROLÜ: {ad} — yem takvimi dolmuş olabilir ({alinan})\n"
                f"   📞 {tel} | İlk yem hatırı: {yem_tarihi.strftime('%d.%m.%Y')}"
            )
            herhangi = True

    if not herhangi:
        satirlar.append(
            "☕ Bugün acil bir bakım araması yok. Çayını iç, koduna bak!"
        )
    satirlar.append("-" * 55)
    return "\n".join(satirlar)


def hatirlatmalari_kontrol_et(veri=None, yazdir=True) -> bool:
    """Konsol çıktısı; True = en az bir hatırlatma satırı üretildi."""
    metin = hatirlatma_metni(veri=veri)
    if yazdir:
        print("\n" + metin)
    return "💉 AŞI" in metin or "🍴 YEM" in metin


def _dosya_yolu() -> Path:
    return Path(__file__).resolve().parent.parent / "database" / DOSYA_ADI


def veriyi_topla(canlilar=None):
    from .aksesuar import aksesuarlar
    from .finans import giderler
    from .stok import stoklar

    base = {
        "stoklar": dict(stoklar),
        "giderler": [dict(g) for g in giderler],
        "aksesuarlar": {k: dict(v) for k, v in aksesuarlar.items()},
        "resmi_giderler": [dict(r) for r in resmi_giderler],
        "sarf_malzemeler": {k: dict(v) for k, v in sarf_malzemeler.items()},
        "saglik_urunleri": {k: dict(v) for k, v in saglik_urunleri.items()},
        "imha_kayitlari": [dict(x) for x in imha_kayitlari],
        "sevkiyat_urunleri": {k: dict(v) for k, v in sevkiyat_urunleri.items()},
        "musteriler": [dict(m) for m in musteriler],
    }
    if canlilar is not None:
        base["canlilar"] = [
            {
                "ad": c.ad,
                "tokluk_orani": c.tokluk_orani,
                "toplam_mama_gram": c.toplam_mama_gram,
            }
            for c in canlilar
        ]
    else:
        yol = _dosya_yolu()
        if yol.exists():
            try:
                with open(yol, "r", encoding="utf-8") as f:
                    old = json.load(f)
                if "canlilar" in old:
                    base["canlilar"] = old["canlilar"]
            except (json.JSONDecodeError, OSError, TypeError):
                pass
    return base


def veriyi_uygula(veri: dict) -> None:
    global PENDING_CANLILAR
    from .aksesuar import aksesuarlar
    from .finans import giderler
    from .stok import stoklar

    stoklar.clear()
    stoklar.update(veri.get("stoklar", {}))

    giderler.clear()
    for g in veri.get("giderler", []):
        giderler.append(dict(g))

    aksesuarlar.clear()
    for ad, v in veri.get("aksesuarlar", {}).items():
        aksesuarlar[ad] = dict(v)

    PENDING_CANLILAR = veri.get("canlilar")

    resmi_giderler.clear()
    for r in veri.get("resmi_giderler", []):
        resmi_giderler.append(dict(r))

    sarf_malzemeler.clear()
    for ad, v in veri.get("sarf_malzemeler", {}).items():
        sarf_malzemeler[ad] = dict(v)

    saglik_urunleri.clear()
    for ad, v in veri.get("saglik_urunleri", {}).items():
        saglik_urunleri[ad] = dict(v)

    imha_kayitlari.clear()
    for x in veri.get("imha_kayitlari", []):
        imha_kayitlari.append(dict(x))

    sevkiyat_urunleri.clear()
    for ad, v in veri.get("sevkiyat_urunleri", {}).items():
        sevkiyat_urunleri[ad] = dict(v)

    musteriler.clear()
    for m in veri.get("musteriler", []):
        musteriler.append(dict(m))


def canlilar_uygula(canlilar) -> None:
    global PENDING_CANLILAR
    if not PENDING_CANLILAR:
        return
    by_ad = {c.ad: c for c in canlilar}
    for k in PENDING_CANLILAR:
        ad = k.get("ad")
        if ad in by_ad:
            c = by_ad[ad]
            c.tokluk_orani = float(k.get("tokluk_orani", 50))
            c.toplam_mama_gram = float(k.get("toplam_mama_gram", 0))
            c.tokluk_orani = max(0.0, min(100.0, c.tokluk_orani))
            c.toplam_mama_gram = max(0.0, c.toplam_mama_gram)
    PENDING_CANLILAR = None


def defteri_kaydet(veri=None, yazdir=False):
    if veri is None:
        veri = veriyi_topla()
    with open(_dosya_yolu(), "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)
    if yazdir:
        print(
            "\n💾 KAYIT TAMAM: Tüm veriler maliye denetimine hazır şekilde dosyalandı."
        )


def defteri_yukle():
    yol = _dosya_yolu()
    if os.path.exists(yol):
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "aksesuarlar": {},
        "giderler": [],
        "stoklar": {},
        "resmi_giderler": [],
        "sarf_malzemeler": {},
        "saglik_urunleri": {},
        "imha_kayitlari": [],
        "sevkiyat_urunleri": {},
        "musteriler": [],
    }


def magaza_acilis():
    """İlk çalışmada varsayılanları dosyaya yazar; dosya varsa belleğe yükler."""
    yol = _dosya_yolu()
    if not yol.exists():
        defteri_kaydet(veriyi_topla(), yazdir=False)
        return
    ham = defteri_yukle()
    veriyi_uygula(ham)


def kaydet(canlilar=None):
    """GUI ve sessiz kayıt. canlilar verilirse mama/tokluk da dosyaya yazılır."""
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)


def resmi_gider_isle(kategori, tutar, evrak_no, canlilar=None, yazdir=True):
    """Belediye, veteriner, vergi vb. evrak numaralı resmi gider kaydı."""
    yeni_kayit = {
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kategori": kategori,
        "tutar": float(tutar),
        "evrak_no": evrak_no,
    }
    resmi_giderler.append(yeni_kayit)
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(
            f"🏛️ RESMİ KAYIT: {kategori} için {tutar} TL işlendi. (Evrak: {evrak_no})"
        )
    return yeni_kayit


def sarf_malzeme_ekle(ad, adet, birim_fiyat, canlilar=None, yazdir=True):
    """Sarf / demirbaş kalemi: adet ve birim fiyat (TL) ile deftere işlenir (toplam yazılır)."""
    ad = (ad or "").strip()
    sarf_malzemeler[ad] = {
        "adet": adet,
        "fiyat": float(birim_fiyat),
    }
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(f"📦 SARF GİRİŞİ: {ad} ({adet} adet) envantere eklendi.")


def sarf_stok_ekle(ad, eklenecek_adet, birim_fiyat=None, canlilar=None, yazdir=True):
    """
    Mevcut kaleme adet ekler (sipariş geldi).
    Kalem yoksa yeni açılır; o durumda birim_fiyat zorunlu.
    """
    ad = (ad or "").strip()
    if not ad:
        return False, "Ürün adı boş."
    try:
        ek = float(eklenecek_adet)
    except (TypeError, ValueError):
        return False, "Eklenecek adet sayı olmalı."
    if ek <= 0:
        return False, "Eklenecek adet sıfırdan büyük olmalı."

    if ad in sarf_malzemeler:
        sarf_malzemeler[ad]["adet"] = float(sarf_malzemeler[ad]["adet"]) + ek
        if birim_fiyat is not None:
            sarf_malzemeler[ad]["fiyat"] = float(birim_fiyat)
        top = sarf_malzemeler[ad]["adet"]
        msg = f"📦 STOK ARTIRILDI: {ad} +{ek:g} adet → toplam {top:g} adet."
    else:
        if birim_fiyat is None:
            return False, "Yeni kalem için birim fiyat girin."
        sarf_malzemeler[ad] = {"adet": ek, "fiyat": float(birim_fiyat)}
        msg = f"📦 SARF GİRİŞİ: {ad} ({ek:g} adet) envantere eklendi."

    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(msg)
    return True, msg


def sarf_envanter_dokumu():
    print("\n🔍 GÜNCEL SARF ENVANTERİ:")
    for ad, detay in sarf_malzemeler.items():
        print(
            f"  • {ad.ljust(25)}: {detay['adet']} adet | Birim: {detay['fiyat']} TL"
        )


def skt_durum_ozet(skt_str, kritik_gun=None):
    """SKT string (YYYY-MM-DD) için kısa durum metni ve kalan gün."""
    if kritik_gun is None:
        kritik_gun = SKT_KRITIK_GUN
    skt_d = datetime.strptime(skt_str.strip(), "%Y-%m-%d").date()
    bugun = date.today()
    kalan = (skt_d - bugun).days
    if kalan < 0:
        return "❌ TARİHİ GEÇMİŞ! (İMHA EDİLMELİ)", kalan
    if kalan <= kritik_gun:
        return f"⚠️ DİKKAT: {kalan} GÜN KALDI!", kalan
    return "✅ GÜVENLİ", kalan


def saglik_urunu_ekle(ad, miktar, skt_tarihi, canlilar=None, yazdir=True):
    """Vitamin, kuş kumu vb.; skt_tarihi 'YYYY-MM-DD' formatında olmalı."""
    ad = (ad or "").strip()
    datetime.strptime(skt_tarihi.strip(), "%Y-%m-%d")
    saglik_urunleri[ad] = {"miktar": miktar, "skt": skt_tarihi.strip()}
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(f"💊 SAĞLIK ÜRÜNÜ KAYDI: {ad} ({miktar}) - SKT: {skt_tarihi}")


def skt_kontrol_metni(kritik_gun=None):
    if kritik_gun is None:
        kritik_gun = SKT_KRITIK_GUN
    satirlar = ["", "--- 🩺 SAĞLIK BAKANLIĞI ONAYLI ÜRÜN DENETİMİ ---"]
    for ad, detay in sorted(saglik_urunleri.items()):
        skt = detay.get("skt", "")
        durum, _kalan = skt_durum_ozet(skt, kritik_gun)
        satirlar.append(
            f"  • {ad.ljust(25)} | SKT: {skt} | Durum: {durum}"
        )
    return "\n".join(satirlar)


def skt_kontrol_et(kritik_gun=None, yazdir=True):
    metin = skt_kontrol_metni(kritik_gun)
    if yazdir:
        print(metin)
    return metin


def urun_imha_et(ad, miktar, sebep, canlilar=None, yazdir=True):
    """İmha tutanağı + sağlık envanterinden ürün silinir (ad tam eşleşme)."""
    ad = (ad or "").strip()
    kayit = {
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "urun": ad,
        "miktar": miktar,
        "sebep": sebep,
    }
    imha_kayitlari.append(kayit)
    if ad in saglik_urunleri:
        del saglik_urunleri[ad]
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        tutanak = int(time.time())
        print(
            f"⚠️ İMHA KAYDI: {ad} ({miktar}) — {sebep} "
            f"(Tutanak No: #IMHA-{tutanak})"
        )


def sevkiyat_urunu_ekle(ad, adet, fiyat, canlilar=None, yazdir=True):
    """Taşıma çantası, folluk vb. son envanter kalemi."""
    ad = (ad or "").strip()
    sevkiyat_urunleri[ad] = {"adet": adet, "fiyat": float(fiyat)}
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(f"🏠 SEVKİYAT GİRİŞİ: {ad} ({adet} adet) eklendi.")


def musteri_kaydet(
    ad_soyad, tc_no, telefon, adres, alinan_canli, canlilar=None, yazdir=True
):
    """Sahiplendirme / müşteri kaydı."""
    yeni = {
        "islem_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ad_soyad": (ad_soyad or "").strip(),
        "tc_no": str(tc_no).strip(),
        "telefon": str(telefon).strip(),
        "adres": (adres or "").strip(),
        "alinan_canli": (alinan_canli or "").strip(),
    }
    musteriler.append(yeni)
    defteri_kaydet(veriyi_topla(canlilar=canlilar), yazdir=False)
    if yazdir:
        print(
            f"\n✅ SAHİPLENDİRME KAYDI TAMAM: {alinan_canli} artık {ad_soyad} Bey'e/Hanım'a emanet."
        )
        print(f"📞 İletişim: {telefon} | Takip Listesine Alındı.")


def musteri_sorgula(isim_parcasi, yazdir=True):
    """İsim parçasına göre müşteri listesi (bellek)."""
    parca = (isim_parcasi or "").lower().strip()
    bulunanlar = [
        m
        for m in musteriler
        if parca in (m.get("ad_soyad") or "").lower()
    ]
    if yazdir:
        if bulunanlar:
            print(f"\n🔍 '{isim_parcasi}' ile eşleşen kayıtlar:")
            for m in bulunanlar:
                print(
                    f"👤 {m['ad_soyad']} | Aldığı: {m['alinan_canli']} | Tel: {m['telefon']}"
                )
        else:
            print("\n❌ Kayıt bulunamadı.")
    return bulunanlar


def musteri_sorgu_metni(isim_parcasi):
    """GUI / arama için metin."""
    parca = (isim_parcasi or "").strip()
    if not parca:
        return "İsim veya parça girin."
    bulunanlar = musteri_sorgula(isim_parcasi, yazdir=False)
    if not bulunanlar:
        return f"❌ '{isim_parcasi}' için kayıt bulunamadı."
    satirlar = [f"🔍 '{isim_parcasi}' ile eşleşen kayıtlar:\n"]
    for m in bulunanlar:
        satirlar.append(
            f"👤 {m['ad_soyad']}\n   TC: {m.get('tc_no', '')} | Tel: {m['telefon']}\n"
            f"   Adres: {m.get('adres', '')}\n"
            f"   Aldığı canlı: {m['alinan_canli']} | Tarih: {m.get('islem_tarihi', '')}\n"
        )
    return "\n".join(satirlar)


def yeni_aksesuar_ekle(ad, stok, fiyat):
    from .aksesuar import aksesuarlar

    aksesuarlar[ad] = {"stok": stok, "fiyat": fiyat}
    defteri_kaydet(veriyi_topla(), yazdir=True)


if __name__ == "__main__":
    magaza_acilis()

    print("\n--- 🛡️ GÜVENLİ KAYIT SİSTEMİ AKTİF ---")
    print(
        f"Kankam, şu an 'database/{DOSYA_ADI}' dosyası senin resmi defterin oldu."
    )

    yeni_aksesuar_ekle("Pirinç Kafes", 5, 450)
    yeni_aksesuar_ekle("Jako Özel Yem", 10, 150)
