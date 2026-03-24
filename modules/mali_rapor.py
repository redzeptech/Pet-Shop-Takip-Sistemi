# Ay sonu mali rapor (defter verisi + sembolik ciro)
import pathlib
import sys
import time

_root = pathlib.Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from modules.defter import defteri_yukle

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# Sembolik ciro — ileride ayrı `gelirler` listesi ile değiştirilebilir
ORNEK_CIRO_TL = 12500.0


def mali_rapor_metni(ciro_tl=None):
    """Konsol veya GUI için rapor metnini üretir."""
    if ciro_tl is None:
        ciro_tl = ORNEK_CIRO_TL

    veri = defteri_yukle()

    toplam_gelir = float(ciro_tl)
    toplam_gider = 0.0

    satirler = []
    satirler.append("")
    satirler.append("=" * 50)
    satirler.append("📊 MİZAÇ PETSHOP - AY SONU MALİ RAPORU")
    satirler.append("=" * 50)
    satirler.append(f"📅 Rapor Tarihi: {time.strftime('%d.%m.%Y %H:%M')}")
    satirler.append("-" * 50)

    # Aksesuar: gerçek kâr-zarar için satış başına `gelirler` listesi tutulmalı
    _ = veri.get("aksesuarlar", {})
    satirler.append(
        "📦 Aksesuar stoku: dosyada kayıtlı (satış geliri için `gelirler` listesi önerilir)."
    )
    satirler.append("-" * 50)

    satirler.append("📉 RESMİ GİDERLER DETAYI:")
    for gider in veri.get("resmi_giderler", []):
        t = float(gider.get("tutar", 0))
        toplam_gider += t
        tarih_kisa = (gider.get("tarih") or "")[:10]
        kat = (gider.get("kategori") or "")[:25].ljust(25)
        satirler.append(f"  • {tarih_kisa} | {kat}: {t:8.2f} TL")

    satirler.append("-" * 50)
    satirler.append("📉 GENEL GİDERLER (finans modülü):")
    for g in veri.get("giderler", []):
        m = float(g.get("miktar", 0))
        toplam_gider += m
        kalem = (g.get("kalem") or "")[:30]
        satirler.append(f"  • {kalem}: {m:8.2f} TL")

    if not veri.get("giderler"):
        satirler.append("  (kayıt yok)")

    satirler.append("-" * 50)
    satirler.append(f"💰 TOPLAM CİRO (Gelir)  : {toplam_gelir:10.2f} TL")
    satirler.append(f"💸 TOPLAM GİDER         : {toplam_gider:10.2f} TL")
    satirler.append("-" * 50)

    net_kar = toplam_gelir - toplam_gider

    if net_kar > 0:
        satirler.append(f"✅ NET KÂR              : {net_kar:10.2f} TL")
        satirler.append("💡 Not: Kankam dükkan dönüyor, kombiyi biraz açabiliriz! :)")
    else:
        satirler.append(f"❌ NET ZARAR            : {abs(net_kar):10.2f} TL")
        satirler.append("💡 Not: Kemerleri sıkalım, Jako'ya söyle daha az konuşsun!")

    satirler.append("=" * 50)

    return "\n".join(satirler)


def mali_rapor_olustur(ciro_tl=None):
    """Konsola yazdırır."""
    print(mali_rapor_metni(ciro_tl=ciro_tl))


if __name__ == "__main__":
    mali_rapor_olustur()
