import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


class Kus:
    def __init__(self, ad, tur, yetenek):
        self.ad = ad
        self.tur = tur
        self.yetenek = yetenek
        self.neseli_mi = True
        self.ogrenilenler = []

    def kelime_ogret(self, metin):
        if self.tur != "Jako Papağanı":
            return
        m = (metin or "").strip()
        if m:
            self.ogrenilenler.append(m)

    def ses_cikar(self):
        if self.tur == "Jako Papağanı":
            temel = f"🦜 {self.ad} (Jako): 'Liyakat şart kankam, sistem tıkır tıkır!'"
            if self.ogrenilenler:
                ek = random.choice(self.ogrenilenler)
                return f"{temel} — Öğrendiklerimden: '{ek}'"
            return temel
        elif self.tur == "Kanarya":
            return f"🐥 {self.ad} (Kanarya): 'Trililili... Huzur burada!'"
        else:
            return f"🐦 {self.ad} (Muhabbet): 'Cici kuş, cici kuş! 07:00 mesaisi başlasın!'"


# Dükkanın Kanatlı Misafirleri
kus_listesi = [
    Kus("Maviş", "Muhabbet Kuşu", "Takla atar"),
    Kus("Profesör", "Jako Papağanı", "Analiz yapar, doğruları söler"),
    Kus("Paşa", "Kanarya", "Senfoni verir"),
]


if __name__ == "__main__":
    print("--- 🏠 Pet Shop: Kuş Cenneti Bölümü Aktif ---")
    print("Durum: %100 Dürüstlük, %0 İsraf.\n")

    for kus in kus_listesi:
        print(kus.ses_cikar())
        print(f"   > Özel Yeteneği: {kus.yetenek}")
        print("-" * 40)

    print(
        "\nKankam, bak Jako bile 'Liyakat' diyor! Bu dükkanda kimse kimsenin hakkını yemez."
    )
