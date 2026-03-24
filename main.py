"""Pet Shop — ana giriş (tkinter masaüstü). Veri: database/database/petshop_defteri.json"""
import pathlib
import sys
from datetime import date, datetime

import tkinter as tk
from tkinter import ttk

_root = pathlib.Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from modules.aksesuar import (
    AKSESUAR_STOK_UYARI_ESIK,
    aksesuar_satis,
    aksesuar_stok_ekle,
    aksesuarlar,
)
from modules.defter import (
    SKT_KRITIK_GUN,
    canlilar_uygula,
    hatirlatma_metni,
    imha_kayitlari,
    kaydet,
    magaza_acilis,
    musteri_kaydet,
    musteri_sorgu_metni,
    musteriler,
    resmi_gider_isle,
    resmi_giderler,
    saglik_urunleri,
    saglik_urunu_ekle,
    sarf_malzeme_ekle,
    sarf_malzemeler,
    sarf_stok_ekle,
    sevkiyat_urunleri,
    sevkiyat_urunu_ekle,
    skt_durum_ozet,
    skt_kontrol_metni,
    urun_imha_et,
)
from modules.finans import GIDER_UYARI_ESIK, gider_ekle, giderler, toplam_gider_hesapla
from modules.kus_cenneti import kus_listesi
from modules.mali_rapor import mali_rapor_metni
from modules.stok import STOCK_UYARI_ESIK, satis_yap, stoklar

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# --- Şeffaf maliyet: tek kaynak, gram başına TL (tüm türlerde aynı hesap) ---
MAMA_GRAM_BASINA_TL = 0.42

# Zamanla tokluk düşer (acılma artar)
ACILMA_TICK_MS = 1500
TOKLUK_DUSUS_PER_TICK = 1.2
BESLEME_TOKLUK_ARTIS = 22

# Her gün yerel saat 07:00 — kuşlar otomatik öter (uygulama açıksa)
SABAH_SAAT = 7
SABAH_DAKIKA = 0
SABAH_ZAMANLAYICI_MS = 15_000

# Acılma döngüsünde bu kadar tikte bir (~60 sn) canlılar diske yazılır
ACILMA_KAYDET_ARALIK = 40


class Canli:
    def __init__(self, ad, tur, porsiyon_gram):
        self.ad = ad
        self.tur = tur
        self.porsiyon_gram = porsiyon_gram
        self.tokluk_orani = 50.0
        self.toplam_mama_gram = 0.0

    def acilma_adimi(self):
        self.tokluk_orani = max(0.0, self.tokluk_orani - TOKLUK_DUSUS_PER_TICK)

    def besle(self):
        g = self.porsiyon_gram
        self.toplam_mama_gram += g
        self.tokluk_orani = min(100.0, self.tokluk_orani + BESLEME_TOKLUK_ARTIS)
        return g

    @property
    def acilma_yuzdesi(self):
        return 100.0 - self.tokluk_orani

    def maliyet_tl(self):
        return self.toplam_mama_gram * MAMA_GRAM_BASINA_TL


class PetShopApp:
    def __init__(self, root):
        self.root = root
        root.title(
            "Pet Shop — Dükkan, Stok, Aksesuar, Sarf, Sağlık, Müşteri & Finans"
        )
        root.minsize(780, 540)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)
        tab_dukkan = ttk.Frame(notebook)
        tab_stok = ttk.Frame(notebook)
        tab_aksesuar = ttk.Frame(notebook)
        tab_sarf = ttk.Frame(notebook)
        tab_saglik = ttk.Frame(notebook)
        tab_b6 = ttk.Frame(notebook)
        tab_musteri = ttk.Frame(notebook)
        tab_finans = ttk.Frame(notebook)
        notebook.add(tab_dukkan, text="Dükkan")
        notebook.add(tab_stok, text="Yem stokları")
        notebook.add(tab_aksesuar, text="Aksesuar")
        notebook.add(tab_sarf, text="Sarf & demirbaş")
        notebook.add(tab_saglik, text="Sağlık (SKT)")
        notebook.add(tab_b6, text="İmha & sevkiyat")
        notebook.add(tab_musteri, text="Müşteri")
        notebook.add(tab_finans, text="Finans")

        self.canlilar = [
            Canli("Paşa", "Muhabbet Kuşu", 6),
            Canli("Duman", "Kedi", 30),
            Canli("Goldie", "Japon Balığı", 2),
        ]
        canlilar_uygula(self.canlilar)
        self._acilma_sayac = 0

        self._kartlar = []

        ust = ttk.Frame(tab_dukkan, padding=10)
        ust.pack(fill=tk.X)
        ttk.Label(
            ust,
            text="Tokluk zamanla düşer (acılma artar). Besle: porsiyon gramı sabit; maliyet = gram × birim fiyat.",
            wraplength=520,
        ).pack(side=tk.LEFT, anchor=tk.W)
        ust_btn = ttk.Frame(ust)
        ust_btn.pack(side=tk.RIGHT)
        ttk.Button(ust_btn, text="Kuşları dinle", command=self._kuslari_dinle).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(ust_btn, text="Hepsini besle", command=self._tumunu_besle).pack(side=tk.LEFT)

        fiyat = ttk.Frame(tab_dukkan, padding=(10, 0))
        fiyat.pack(fill=tk.X)
        ttk.Label(
            fiyat,
            text=f"Birim fiyat (şeffaf): {MAMA_GRAM_BASINA_TL:.2f} TL / gram mama",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W)

        zaman = ttk.Frame(tab_dukkan, padding=(10, 4))
        zaman.pack(fill=tk.X)
        ttk.Label(
            zaman,
            text=(
                f"Sabah ötüşü: Uygulama açıkken her gün {SABAH_SAAT:02d}:{SABAH_DAKIKA:02d} "
                "(yerel saat) kuşlar otomatik öter — eski mesai saatin, şimdi neşe."
            ),
            wraplength=680,
        ).pack(anchor=tk.W)

        jako_cerceve = ttk.LabelFrame(
            tab_dukkan,
            text="Profesör (Jako Papağanı) — dürüst analiz öğret",
            padding=8,
        )
        jako_cerceve.pack(fill=tk.X, padx=10, pady=(0, 4))
        jako_satir = ttk.Frame(jako_cerceve)
        jako_satir.pack(fill=tk.X)
        self.jako_entry = ttk.Entry(jako_satir, width=60)
        self.jako_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(jako_satir, text="Öğret", command=self._jako_kelime_ogret).pack(side=tk.LEFT)
        self.jako_durum = ttk.Label(jako_cerceve, text="", foreground="#2e7d32")
        self.jako_durum.pack(anchor=tk.W, pady=(6, 0))

        kart_alan = ttk.Frame(tab_dukkan, padding=10)
        kart_alan.pack(fill=tk.BOTH, expand=True)

        for c in self.canlilar:
            self._kartlar.append(self._kart_olustur(kart_alan, c))

        tablo_cerceve = ttk.LabelFrame(
            tab_dukkan, text="Mama tüketimi & maliyet tablosu", padding=10
        )
        tablo_cerceve.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        kolonlar = ("hayvan", "tur", "gram", "birim", "tutar")
        self.tree = ttk.Treeview(tablo_cerceve, columns=kolonlar, show="headings", height=5)
        self.tree.heading("hayvan", text="Hayvan")
        self.tree.heading("tur", text="Tür")
        self.tree.heading("gram", text="Toplam mama (g)")
        self.tree.heading("birim", text="TL / g")
        self.tree.heading("tutar", text="Tutar (TL)")
        self.tree.column("hayvan", width=120)
        self.tree.column("tur", width=140)
        self.tree.column("gram", width=110, anchor=tk.E)
        self.tree.column("birim", width=80, anchor=tk.E)
        self.tree.column("tutar", width=90, anchor=tk.E)
        sb = ttk.Scrollbar(tablo_cerceve, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.toplam_label = ttk.Label(tablo_cerceve, text="", font=("Segoe UI", 10, "bold"))
        self.toplam_label.pack(anchor=tk.E, pady=(8, 0))

        stok_ust = ttk.LabelFrame(
            tab_stok,
            text="Güncel stok durumu (07:00 tarzı kontrol)",
            padding=10,
        )
        stok_ust.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        sk = ("urun", "miktar", "durum")
        self.stok_tree = ttk.Treeview(
            stok_ust, columns=sk, show="headings", height=8
        )
        self.stok_tree.heading("urun", text="Ürün")
        self.stok_tree.heading("miktar", text="Miktar")
        self.stok_tree.heading("durum", text="Durum")
        self.stok_tree.column("urun", width=280)
        self.stok_tree.column("miktar", width=100, anchor=tk.E)
        self.stok_tree.column("durum", width=140)
        stok_sb = ttk.Scrollbar(
            stok_ust, orient=tk.VERTICAL, command=self.stok_tree.yview
        )
        self.stok_tree.configure(yscrollcommand=stok_sb.set)
        self.stok_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stok_sb.pack(side=tk.RIGHT, fill=tk.Y)

        stok_sat = ttk.LabelFrame(tab_stok, text="Satış", padding=10)
        stok_sat.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(stok_sat, text="Ürün:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.stok_urun_combo = ttk.Combobox(
            stok_sat,
            values=list(stoklar.keys()),
            width=48,
            state="readonly",
        )
        self.stok_urun_combo.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        if stoklar:
            self.stok_urun_combo.current(0)

        ttk.Label(stok_sat, text="Miktar:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stok_miktar_entry = ttk.Entry(stok_sat, width=16)
        self.stok_miktar_entry.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        self.stok_miktar_entry.insert(0, "1")

        ttk.Button(stok_sat, text="Satış yap", command=self._stok_satis_yap).grid(
            row=2, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        stok_sat.columnconfigure(1, weight=1)

        self.stok_mesaj = ttk.Label(stok_sat, text="", wraplength=560)
        self.stok_mesaj.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        aks_liste = ttk.LabelFrame(
            tab_aksesuar,
            text="Aksesuar & sarf — güncel stok",
            padding=10,
        )
        aks_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        ak_kol = ("urun", "stok", "fiyat", "durum")
        self.aks_tree = ttk.Treeview(
            aks_liste, columns=ak_kol, show="headings", height=7
        )
        self.aks_tree.heading("urun", text="Ürün")
        self.aks_tree.heading("stok", text="Stok (adet)")
        self.aks_tree.heading("fiyat", text="Birim fiyat (TL)")
        self.aks_tree.heading("durum", text="Durum")
        self.aks_tree.column("urun", width=260)
        self.aks_tree.column("stok", width=90, anchor=tk.E)
        self.aks_tree.column("fiyat", width=110, anchor=tk.E)
        self.aks_tree.column("durum", width=130)
        aks_sb = ttk.Scrollbar(
            aks_liste, orient=tk.VERTICAL, command=self.aks_tree.yview
        )
        self.aks_tree.configure(yscrollcommand=aks_sb.set)
        self.aks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        aks_sb.pack(side=tk.RIGHT, fill=tk.Y)

        _aks_urunler = list(aksesuarlar.keys())

        aks_giris = ttk.LabelFrame(tab_aksesuar, text="Stok girişi (sipariş / teslimat)", padding=10)
        aks_giris.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Label(aks_giris, text="Ürün:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.aks_stok_urun = ttk.Combobox(
            aks_giris,
            values=_aks_urunler,
            width=44,
            state="readonly",
        )
        self.aks_stok_urun.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        if _aks_urunler:
            self.aks_stok_urun.current(0)
        ttk.Label(aks_giris, text="Eklenecek adet:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.aks_stok_adet = ttk.Entry(aks_giris, width=12)
        self.aks_stok_adet.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        self.aks_stok_adet.insert(0, "1")
        ttk.Button(aks_giris, text="Stok ekle", command=self._aksesuar_stok_ekle_gui).grid(
            row=2, column=1, sticky=tk.W, padx=(8, 0), pady=(6, 0)
        )
        aks_giris.columnconfigure(1, weight=1)

        aks_sat = ttk.LabelFrame(tab_aksesuar, text="Satış", padding=10)
        aks_sat.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Label(aks_sat, text="Ürün:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.aks_sat_urun = ttk.Combobox(
            aks_sat,
            values=_aks_urunler,
            width=44,
            state="readonly",
        )
        self.aks_sat_urun.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        if _aks_urunler:
            self.aks_sat_urun.current(0)
        ttk.Label(aks_sat, text="Adet:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.aks_sat_adet = ttk.Entry(aks_sat, width=12)
        self.aks_sat_adet.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        self.aks_sat_adet.insert(0, "1")
        ttk.Button(aks_sat, text="Satış yap", command=self._aksesuar_satis_gui).grid(
            row=2, column=1, sticky=tk.W, padx=(8, 0), pady=(6, 0)
        )
        aks_sat.columnconfigure(1, weight=1)
        self.aks_mesaj = ttk.Label(aks_sat, text="", wraplength=560)
        self.aks_mesaj.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        sarf_liste = ttk.LabelFrame(
            tab_sarf,
            text="Bölüm 4 — Sarf malzeme ve demirbaş (envanter)",
            padding=10,
        )
        sarf_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        skol = ("ad", "adet", "birim")
        self.sarf_tree = ttk.Treeview(
            sarf_liste, columns=skol, show="headings", height=10
        )
        self.sarf_tree.heading("ad", text="Ürün")
        self.sarf_tree.heading("adet", text="Adet")
        self.sarf_tree.heading("birim", text="Birim fiyat (TL)")
        self.sarf_tree.column("ad", width=320)
        self.sarf_tree.column("adet", width=90, anchor=tk.E)
        self.sarf_tree.column("birim", width=120, anchor=tk.E)
        sarf_sb = ttk.Scrollbar(
            sarf_liste, orient=tk.VERTICAL, command=self.sarf_tree.yview
        )
        self.sarf_tree.configure(yscrollcommand=sarf_sb.set)
        self.sarf_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sarf_sb.pack(side=tk.RIGHT, fill=tk.Y)

        sarf_form = ttk.LabelFrame(tab_sarf, text="Yeni kalem (giriş / güncelleme)", padding=10)
        sarf_form.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Label(sarf_form, text="Ad:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sarf_ad = ttk.Entry(sarf_form, width=50)
        self.sarf_ad.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(sarf_form, text="Adet:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sarf_adet = ttk.Entry(sarf_form, width=14)
        self.sarf_adet.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(sarf_form, text="Birim fiyat (TL):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sarf_birim = ttk.Entry(sarf_form, width=14)
        self.sarf_birim.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(
            sarf_form,
            text="Kaydet = toplam adet yazar. Stok artır = mevcut adete ekler (adet kutusuna eklenecek miktar).",
            foreground="#555",
            wraplength=520,
            font=("Segoe UI", 9),
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))
        sarf_btn = ttk.Frame(sarf_form)
        sarf_btn.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Button(sarf_btn, text="Kaydet (toplam)", command=self._sarf_kaydet_gui).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(sarf_btn, text="Stok artır", command=self._sarf_stok_artir_gui).pack(
            side=tk.LEFT
        )
        sarf_form.columnconfigure(1, weight=1)
        self.sarf_mesaj = ttk.Label(sarf_form, text="", wraplength=560)
        self.sarf_mesaj.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        sag_liste = ttk.LabelFrame(
            tab_saglik,
            text="Bölüm 5 — Vitamin & kuş kumu (SKT takibi)",
            padding=10,
        )
        sag_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        sgk = ("ad", "miktar", "skt", "durum")
        self.sag_tree = ttk.Treeview(
            sag_liste, columns=sgk, show="headings", height=8
        )
        self.sag_tree.heading("ad", text="Ürün")
        self.sag_tree.heading("miktar", text="Miktar")
        self.sag_tree.heading("skt", text="SKT (YYYY-MM-DD)")
        self.sag_tree.heading("durum", text="Durum")
        self.sag_tree.column("ad", width=240)
        self.sag_tree.column("miktar", width=70, anchor=tk.E)
        self.sag_tree.column("skt", width=110)
        self.sag_tree.column("durum", width=260)
        sag_sb = ttk.Scrollbar(
            sag_liste, orient=tk.VERTICAL, command=self.sag_tree.yview
        )
        self.sag_tree.configure(yscrollcommand=sag_sb.set)
        self.sag_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sag_sb.pack(side=tk.RIGHT, fill=tk.Y)

        sag_form = ttk.LabelFrame(tab_saglik, text="Yeni / güncelle (aynı ad üzerine yazar)", padding=10)
        sag_form.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Label(sag_form, text="Ürün adı:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sag_ad = ttk.Entry(sag_form, width=48)
        self.sag_ad.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(sag_form, text="Miktar:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sag_miktar = ttk.Entry(sag_form, width=14)
        self.sag_miktar.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(sag_form, text="SKT (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sag_skt = ttk.Entry(sag_form, width=14)
        self.sag_skt.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        sag_btn = ttk.Frame(sag_form)
        sag_btn.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Button(sag_btn, text="Kaydet", command=self._saglik_kaydet_gui).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(sag_btn, text="SKT denetimi raporu", command=self._skt_raporu_goster).pack(
            side=tk.LEFT
        )
        sag_form.columnconfigure(1, weight=1)
        self.sag_mesaj = ttk.Label(sag_form, text="", wraplength=560)
        self.sag_mesaj.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        b6_imha = ttk.LabelFrame(
            tab_b6,
            text="Bölüm 6 — İmha tutanağı (sağlık envanterinden düşer)",
            padding=10,
        )
        b6_imha.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        ik = ("tarih", "urun", "miktar", "sebep")
        self.imha_tree = ttk.Treeview(
            b6_imha, columns=ik, show="headings", height=4
        )
        self.imha_tree.heading("tarih", text="Tarih")
        self.imha_tree.heading("urun", text="Ürün")
        self.imha_tree.heading("miktar", text="Miktar")
        self.imha_tree.heading("sebep", text="Sebep")
        self.imha_tree.column("tarih", width=130)
        self.imha_tree.column("urun", width=200)
        self.imha_tree.column("miktar", width=70, anchor=tk.E)
        self.imha_tree.column("sebep", width=240)
        imha_sb = ttk.Scrollbar(
            b6_imha, orient=tk.VERTICAL, command=self.imha_tree.yview
        )
        self.imha_tree.configure(yscrollcommand=imha_sb.set)
        self.imha_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        imha_sb.pack(side=tk.RIGHT, fill=tk.Y)

        imha_form = ttk.LabelFrame(tab_b6, text="Yeni imha kaydı", padding=10)
        imha_form.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Label(imha_form, text="Ürün (sağlık listesiyle aynı ad):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.imha_ad = ttk.Entry(imha_form, width=44)
        self.imha_ad.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(imha_form, text="Miktar:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.imha_miktar = ttk.Entry(imha_form, width=12)
        self.imha_miktar.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(imha_form, text="Sebep:").grid(row=2, column=0, sticky=tk.NW, pady=2)
        self.imha_sebep = ttk.Entry(imha_form, width=44)
        self.imha_sebep.grid(row=2, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Button(imha_form, text="İmha kaydet", command=self._imha_gui).grid(
            row=3, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        imha_form.columnconfigure(1, weight=1)
        self.imha_mesaj = ttk.Label(imha_form, text="", wraplength=520)
        self.imha_mesaj.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        b6_sev = ttk.LabelFrame(
            tab_b6,
            text="Sevkiyat / son envanter (taşıma, folluk vb.)",
            padding=10,
        )
        b6_sev.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        svk = ("ad", "adet", "fiyat")
        self.sev_tree = ttk.Treeview(
            b6_sev, columns=svk, show="headings", height=4
        )
        self.sev_tree.heading("ad", text="Ürün")
        self.sev_tree.heading("adet", text="Adet")
        self.sev_tree.heading("fiyat", text="Birim (TL)")
        self.sev_tree.column("ad", width=300)
        self.sev_tree.column("adet", width=80, anchor=tk.E)
        self.sev_tree.column("fiyat", width=100, anchor=tk.E)
        sev_sb = ttk.Scrollbar(b6_sev, orient=tk.VERTICAL, command=self.sev_tree.yview)
        self.sev_tree.configure(yscrollcommand=sev_sb.set)
        self.sev_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sev_sb.pack(side=tk.RIGHT, fill=tk.Y)

        sev_form = ttk.LabelFrame(tab_b6, text="Yeni sevkiyat kalemi", padding=10)
        sev_form.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Label(sev_form, text="Ad:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sev_ad = ttk.Entry(sev_form, width=44)
        self.sev_ad.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(sev_form, text="Adet:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sev_adet = ttk.Entry(sev_form, width=12)
        self.sev_adet.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(sev_form, text="Birim fiyat (TL):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sev_fiyat = ttk.Entry(sev_form, width=12)
        self.sev_fiyat.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Button(sev_form, text="Kaydet", command=self._sevkiyat_gui).grid(
            row=3, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        sev_form.columnconfigure(1, weight=1)
        self.sev_mesaj = ttk.Label(sev_form, text="", wraplength=520)
        self.sev_mesaj.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        mus_liste = ttk.LabelFrame(
            tab_musteri,
            text="Sahiplendirme / müşteri kayıtları (deftere işlenir)",
            padding=10,
        )
        mus_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))
        mk = ("tarih", "ad_soyad", "tc_no", "telefon", "alinan_canli")
        self.musteri_tree = ttk.Treeview(
            mus_liste, columns=mk, show="headings", height=8
        )
        self.musteri_tree.heading("tarih", text="Tarih")
        self.musteri_tree.heading("ad_soyad", text="Ad soyad")
        self.musteri_tree.heading("tc_no", text="TC")
        self.musteri_tree.heading("telefon", text="Telefon")
        self.musteri_tree.heading("alinan_canli", text="Alınan canlı")
        self.musteri_tree.column("tarih", width=130)
        self.musteri_tree.column("ad_soyad", width=160)
        self.musteri_tree.column("tc_no", width=100)
        self.musteri_tree.column("telefon", width=120)
        self.musteri_tree.column("alinan_canli", width=220)
        mus_sb = ttk.Scrollbar(
            mus_liste, orient=tk.VERTICAL, command=self.musteri_tree.yview
        )
        self.musteri_tree.configure(yscrollcommand=mus_sb.set)
        self.musteri_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mus_sb.pack(side=tk.RIGHT, fill=tk.Y)

        mus_form = ttk.LabelFrame(tab_musteri, text="Yeni sahiplendirme kaydı", padding=10)
        mus_form.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Label(mus_form, text="Ad soyad:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mus_ad = ttk.Entry(mus_form, width=44)
        self.mus_ad.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(mus_form, text="TC:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mus_tc = ttk.Entry(mus_form, width=20)
        self.mus_tc.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(mus_form, text="Telefon:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mus_tel = ttk.Entry(mus_form, width=24)
        self.mus_tel.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(mus_form, text="Adres:").grid(row=3, column=0, sticky=tk.NW, pady=2)
        self.mus_adres = tk.Text(mus_form, width=50, height=3, font=("Segoe UI", 10))
        self.mus_adres.grid(row=3, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(mus_form, text="Alınan canlı:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.mus_canli = ttk.Entry(mus_form, width=44)
        self.mus_canli.grid(row=4, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        mus_btn = ttk.Frame(mus_form)
        mus_btn.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        ttk.Button(mus_btn, text="Kaydet", command=self._musteri_kaydet_gui).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        mus_form.columnconfigure(1, weight=1)
        self.mus_mesaj = ttk.Label(mus_form, text="", wraplength=560)
        self.mus_mesaj.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        mus_ara = ttk.LabelFrame(tab_musteri, text="İsim ile ara", padding=10)
        mus_ara.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Label(mus_ara, text="İsim parçası:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.mus_ara_entry = ttk.Entry(mus_ara, width=36)
        self.mus_ara_entry.grid(row=0, column=1, sticky=tk.W, padx=(8, 8), pady=2)
        ttk.Button(mus_ara, text="Ara", command=self._musteri_ara_goster).grid(
            row=0, column=2, sticky=tk.W, pady=2
        )

        resmi_cerceve = ttk.LabelFrame(
            tab_finans,
            text="Resmi defter (Bölüm 3) — Belediye, veteriner, vergi (evrak no)",
            padding=10,
        )
        resmi_cerceve.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        rk = ("tarih", "kategori", "tutar", "evrak")
        self.resmi_tree = ttk.Treeview(
            resmi_cerceve, columns=rk, show="headings", height=4
        )
        self.resmi_tree.heading("tarih", text="Tarih")
        self.resmi_tree.heading("kategori", text="Kategori")
        self.resmi_tree.heading("tutar", text="Tutar (TL)")
        self.resmi_tree.heading("evrak", text="Evrak no")
        self.resmi_tree.column("tarih", width=150)
        self.resmi_tree.column("kategori", width=220)
        self.resmi_tree.column("tutar", width=90, anchor=tk.E)
        self.resmi_tree.column("evrak", width=140)
        resmi_sb = ttk.Scrollbar(
            resmi_cerceve, orient=tk.VERTICAL, command=self.resmi_tree.yview
        )
        self.resmi_tree.configure(yscrollcommand=resmi_sb.set)
        self.resmi_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        resmi_sb.pack(side=tk.RIGHT, fill=tk.Y)

        resmi_form = ttk.LabelFrame(tab_finans, text="Yeni resmi kayıt", padding=10)
        resmi_form.pack(fill=tk.X, padx=10, pady=(0, 4))
        ttk.Label(resmi_form, text="Kategori:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.resmi_kategori = ttk.Entry(resmi_form, width=48)
        self.resmi_kategori.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        ttk.Label(resmi_form, text="Tutar (TL):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.resmi_tutar = ttk.Entry(resmi_form, width=16)
        self.resmi_tutar.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Label(resmi_form, text="Evrak no:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.resmi_evrak = ttk.Entry(resmi_form, width=32)
        self.resmi_evrak.grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=2)
        ttk.Button(resmi_form, text="Resmi kayıt ekle", command=self._resmi_kayit_ekle).grid(
            row=3, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        resmi_form.columnconfigure(1, weight=1)
        self.resmi_mesaj = ttk.Label(resmi_form, text="", wraplength=560)
        self.resmi_mesaj.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        fin_liste = ttk.LabelFrame(
            tab_finans,
            text="Genel giderler (kalem / not)",
            padding=10,
        )
        fin_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        fk = ("kalem", "miktar", "not")
        self.fin_tree = ttk.Treeview(
            fin_liste, columns=fk, show="headings", height=6
        )
        self.fin_tree.heading("kalem", text="Kalem")
        self.fin_tree.heading("miktar", text="Miktar (TL)")
        self.fin_tree.heading("not", text="Açıklama")
        self.fin_tree.column("kalem", width=180)
        self.fin_tree.column("miktar", width=100, anchor=tk.E)
        self.fin_tree.column("not", width=360)
        fin_sb = ttk.Scrollbar(
            fin_liste, orient=tk.VERTICAL, command=self.fin_tree.yview
        )
        self.fin_tree.configure(yscrollcommand=fin_sb.set)
        self.fin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fin_sb.pack(side=tk.RIGHT, fill=tk.Y)

        fin_form = ttk.LabelFrame(tab_finans, text="Yeni genel gider", padding=10)
        fin_form.pack(fill=tk.X, padx=10, pady=(0, 4))

        ttk.Label(fin_form, text="Kalem:").grid(row=0, column=0, sticky=tk.NW, pady=2)
        self.fin_kalem = ttk.Entry(fin_form, width=50)
        self.fin_kalem.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ttk.Label(fin_form, text="Miktar (TL):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fin_miktar = ttk.Entry(fin_form, width=16)
        self.fin_miktar.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=2)

        ttk.Label(fin_form, text="Açıklama:").grid(row=2, column=0, sticky=tk.NW, pady=2)
        self.fin_not = tk.Text(fin_form, width=50, height=3, font=("Segoe UI", 10))
        self.fin_not.grid(row=2, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ttk.Button(fin_form, text="Gider ekle", command=self._finans_gider_ekle).grid(
            row=3, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        fin_form.columnconfigure(1, weight=1)

        self.fin_mesaj = ttk.Label(fin_form, text="", wraplength=560)
        self.fin_mesaj.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        fin_rapor_btn = ttk.Frame(tab_finans, padding=(10, 4))
        fin_rapor_btn.pack(fill=tk.X)
        ttk.Button(
            fin_rapor_btn,
            text="Ay sonu mali raporu",
            command=self._mali_rapor_goster,
        ).pack(side=tk.LEFT)

        fin_alt = ttk.Frame(tab_finans, padding=(10, 0, 10, 10))
        fin_alt.pack(fill=tk.X)
        self.fin_toplam = ttk.Label(
            fin_alt, text="", font=("Segoe UI", 10, "bold")
        )
        self.fin_toplam.pack(anchor=tk.W)
        self.fin_uyari = ttk.Label(fin_alt, text="", wraplength=640)
        self.fin_uyari.pack(anchor=tk.W, pady=(4, 0))

        self._dongu_id = None
        self._sabah_timer_id = None
        self._son_sabah_otusu_tarihi = None
        self._dongu_baslat()
        self._sabah_zamanlayici_baslat()
        self._arayuzu_guncelle()
        self._stok_tablo_guncelle()
        self._aksesuar_tablo_guncelle()
        self._sarf_tablo_guncelle()
        self._saglik_tablo_guncelle()
        self._imha_tablo_guncelle()
        self._sevkiyat_tablo_guncelle()
        self._musteri_tablo_guncelle()
        self._finans_tablo_guncelle()
        self._resmi_tablo_guncelle()
        self.root.after(250, self._hatirlatma_penceresi)

    def _hatirlatma_penceresi(self):
        win = tk.Toplevel(self.root)
        win.title("🔔 HATIRLATMA")
        win.minsize(520, 360)
        win.transient(self.root)
        cerceve = ttk.Frame(win, padding=10)
        cerceve.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(
            cerceve,
            wrap=tk.WORD,
            width=72,
            height=18,
            font=("Consolas", 10),
        )
        sb = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.insert(tk.END, hatirlatma_metni())
        txt.config(state=tk.DISABLED)
        btnf = ttk.Frame(win, padding=(10, 0, 10, 10))
        btnf.pack(fill=tk.X)
        ttk.Button(btnf, text="Tamam", command=win.destroy).pack(side=tk.RIGHT)

    def _saglik_tablo_guncelle(self):
        for item in self.sag_tree.get_children():
            self.sag_tree.delete(item)
        for ad, detay in sorted(saglik_urunleri.items()):
            skt = detay.get("skt", "")
            try:
                durum, _k = skt_durum_ozet(skt, SKT_KRITIK_GUN)
            except (ValueError, TypeError):
                durum = "⚠️ SKT formatı?"
            self.sag_tree.insert(
                "",
                "end",
                values=(
                    ad,
                    f"{detay.get('miktar', '')}",
                    skt,
                    durum,
                ),
            )

    def _saglik_kaydet_gui(self):
        ad = self.sag_ad.get().strip()
        if not ad:
            self.sag_mesaj.config(text="Ürün adı girin.", foreground="#c62828")
            return
        ham_m = self.sag_miktar.get().strip().replace(",", ".")
        skt = self.sag_skt.get().strip()
        if not skt:
            self.sag_mesaj.config(text="SKT girin (YYYY-MM-DD).", foreground="#c62828")
            return
        try:
            miktar = float(ham_m)
        except ValueError:
            self.sag_mesaj.config(text="Miktar sayı olmalı.", foreground="#c62828")
            return
        if miktar < 0:
            self.sag_mesaj.config(text="Miktar negatif olamaz.", foreground="#c62828")
            return
        try:
            saglik_urunu_ekle(ad, miktar, skt, canlilar=self.canlilar, yazdir=False)
        except ValueError:
            self.sag_mesaj.config(
                text="SKT formatı YYYY-MM-DD olmalı.", foreground="#c62828"
            )
            return
        self.sag_ad.delete(0, tk.END)
        self.sag_miktar.delete(0, tk.END)
        self.sag_skt.delete(0, tk.END)
        self.sag_mesaj.config(
            text="Kayıt database/petshop_defteri.json dosyasına işlendi.",
            foreground="#2e7d32",
        )
        self._saglik_tablo_guncelle()

    def _skt_raporu_goster(self):
        win = tk.Toplevel(self.root)
        win.title("SKT denetimi")
        win.minsize(520, 360)
        win.transient(self.root)
        cerceve = ttk.Frame(win, padding=10)
        cerceve.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(
            cerceve,
            wrap=tk.WORD,
            width=72,
            height=20,
            font=("Consolas", 10),
        )
        sb = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.insert(tk.END, skt_kontrol_metni(SKT_KRITIK_GUN))
        txt.config(state=tk.DISABLED)
        ttk.Label(
            win,
            text=f"Kritik uyarı eşiği: {SKT_KRITIK_GUN} gün kala",
            font=("Segoe UI", 9),
        ).pack(pady=(0, 4))
        ttk.Button(win, text="Kapat", command=win.destroy).pack(pady=(0, 10))

    def _imha_tablo_guncelle(self):
        for item in self.imha_tree.get_children():
            self.imha_tree.delete(item)
        for k in imha_kayitlari:
            sebep = k.get("sebep", "") or ""
            if len(sebep) > 50:
                sebep = sebep[:47] + "…"
            self.imha_tree.insert(
                "",
                "end",
                values=(
                    k.get("tarih", ""),
                    k.get("urun", ""),
                    k.get("miktar", ""),
                    sebep,
                ),
            )

    def _sevkiyat_tablo_guncelle(self):
        for item in self.sev_tree.get_children():
            self.sev_tree.delete(item)
        for ad, detay in sorted(sevkiyat_urunleri.items()):
            self.sev_tree.insert(
                "",
                "end",
                values=(
                    ad,
                    f"{detay.get('adet', '')}",
                    f"{float(detay.get('fiyat', 0)):.2f}",
                ),
            )

    def _imha_gui(self):
        ad = self.imha_ad.get().strip()
        if not ad:
            self.imha_mesaj.config(text="Ürün adı girin.", foreground="#c62828")
            return
        ham = self.imha_miktar.get().strip().replace(",", ".")
        try:
            miktar = float(ham)
        except ValueError:
            self.imha_mesaj.config(text="Miktar sayı olmalı.", foreground="#c62828")
            return
        sebep = self.imha_sebep.get().strip()
        if not sebep:
            self.imha_mesaj.config(text="Sebep girin.", foreground="#c62828")
            return
        urun_imha_et(ad, miktar, sebep, canlilar=self.canlilar, yazdir=False)
        self.imha_ad.delete(0, tk.END)
        self.imha_miktar.delete(0, tk.END)
        self.imha_sebep.delete(0, tk.END)
        self.imha_mesaj.config(
            text="İmha kaydı dosyalandı. Sağlık envanterinde ad eşleşirse kalem silindi.",
            foreground="#2e7d32",
        )
        self._imha_tablo_guncelle()
        self._saglik_tablo_guncelle()

    def _sevkiyat_gui(self):
        ad = self.sev_ad.get().strip()
        if not ad:
            self.sev_mesaj.config(text="Ürün adı girin.", foreground="#c62828")
            return
        ham_a = self.sev_adet.get().strip().replace(",", ".")
        ham_f = self.sev_fiyat.get().strip().replace(",", ".")
        try:
            adet = float(ham_a)
            fiyat = float(ham_f)
        except ValueError:
            self.sev_mesaj.config(
                text="Adet ve fiyat sayı olmalı.", foreground="#c62828"
            )
            return
        if adet < 0 or fiyat < 0:
            self.sev_mesaj.config(
                text="Adet ve fiyat negatif olamaz.", foreground="#c62828"
            )
            return
        sevkiyat_urunu_ekle(ad, adet, fiyat, canlilar=self.canlilar, yazdir=False)
        self.sev_ad.delete(0, tk.END)
        self.sev_adet.delete(0, tk.END)
        self.sev_fiyat.delete(0, tk.END)
        self.sev_mesaj.config(
            text="Sevkiyat kalemi database/petshop_defteri.json dosyasına işlendi.",
            foreground="#2e7d32",
        )
        self._sevkiyat_tablo_guncelle()

    def _musteri_tablo_guncelle(self):
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
        for m in reversed(musteriler):
            self.musteri_tree.insert(
                "",
                "end",
                values=(
                    m.get("islem_tarihi", ""),
                    m.get("ad_soyad", ""),
                    m.get("tc_no", ""),
                    m.get("telefon", ""),
                    m.get("alinan_canli", ""),
                ),
            )

    def _musteri_kaydet_gui(self):
        ad_soyad = self.mus_ad.get().strip()
        if not ad_soyad:
            self.mus_mesaj.config(text="Ad soyad girin.", foreground="#c62828")
            return
        alinan = self.mus_canli.get().strip()
        if not alinan:
            self.mus_mesaj.config(text="Alınan canlı bilgisini girin.", foreground="#c62828")
            return
        tel = self.mus_tel.get().strip()
        if not tel:
            self.mus_mesaj.config(text="Telefon girin.", foreground="#c62828")
            return
        tc = self.mus_tc.get().strip()
        adres = self.mus_adres.get("1.0", tk.END).strip()
        musteri_kaydet(
            ad_soyad,
            tc,
            tel,
            adres,
            alinan,
            canlilar=self.canlilar,
            yazdir=False,
        )
        self.mus_ad.delete(0, tk.END)
        self.mus_tc.delete(0, tk.END)
        self.mus_tel.delete(0, tk.END)
        self.mus_adres.delete("1.0", tk.END)
        self.mus_canli.delete(0, tk.END)
        self.mus_mesaj.config(
            text="Kayıt database/petshop_defteri.json dosyasına işlendi.",
            foreground="#2e7d32",
        )
        self._musteri_tablo_guncelle()

    def _musteri_ara_goster(self):
        parca = self.mus_ara_entry.get().strip()
        win = tk.Toplevel(self.root)
        win.title("Müşteri arama")
        win.minsize(480, 320)
        win.transient(self.root)
        cerceve = ttk.Frame(win, padding=10)
        cerceve.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(
            cerceve,
            wrap=tk.WORD,
            width=72,
            height=16,
            font=("Consolas", 10),
        )
        sb = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.insert(tk.END, musteri_sorgu_metni(parca))
        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="Kapat", command=win.destroy).pack(pady=(0, 10))

    def _sarf_tablo_guncelle(self):
        for item in self.sarf_tree.get_children():
            self.sarf_tree.delete(item)
        for ad, detay in sarf_malzemeler.items():
            self.sarf_tree.insert(
                "",
                "end",
                values=(
                    ad,
                    f"{detay.get('adet', 0):g}",
                    f"{float(detay.get('fiyat', 0)):.2f}",
                ),
            )

    def _sarf_kaydet_gui(self):
        ad = self.sarf_ad.get().strip()
        if not ad:
            self.sarf_mesaj.config(text="Ürün adı girin.", foreground="#c62828")
            return
        ham_a = self.sarf_adet.get().strip().replace(",", ".")
        ham_b = self.sarf_birim.get().strip().replace(",", ".")
        try:
            adet = float(ham_a)
            birim = float(ham_b)
        except ValueError:
            self.sarf_mesaj.config(
                text="Adet ve birim fiyat sayı olmalı.", foreground="#c62828"
            )
            return
        if adet < 0 or birim < 0:
            self.sarf_mesaj.config(
                text="Adet ve fiyat negatif olamaz.", foreground="#c62828"
            )
            return
        sarf_malzeme_ekle(ad, adet, birim, canlilar=self.canlilar, yazdir=False)
        self.sarf_ad.delete(0, tk.END)
        self.sarf_adet.delete(0, tk.END)
        self.sarf_birim.delete(0, tk.END)
        self.sarf_mesaj.config(
            text="Toplam adet kaydedildi (database/petshop_defteri.json).",
            foreground="#2e7d32",
        )
        self._sarf_tablo_guncelle()

    def _sarf_stok_artir_gui(self):
        ad = self.sarf_ad.get().strip()
        if not ad:
            self.sarf_mesaj.config(text="Ürün adı girin.", foreground="#c62828")
            return
        ham_a = self.sarf_adet.get().strip().replace(",", ".")
        ham_b = self.sarf_birim.get().strip().replace(",", ".")
        try:
            ek = float(ham_a)
        except ValueError:
            self.sarf_mesaj.config(
                text="Eklenecek adet sayı olmalı.", foreground="#c62828"
            )
            return
        birim = None
        if ham_b:
            try:
                birim = float(ham_b)
            except ValueError:
                self.sarf_mesaj.config(
                    text="Birim fiyat sayı olmalı veya boş bırakın.", foreground="#c62828"
                )
                return
            if birim < 0:
                self.sarf_mesaj.config(
                    text="Birim fiyat negatif olamaz.", foreground="#c62828"
                )
                return
        ok, mesaj = sarf_stok_ekle(
            ad, ek, birim_fiyat=birim, canlilar=self.canlilar, yazdir=False
        )
        self.sarf_mesaj.config(
            text=mesaj,
            foreground="#2e7d32" if ok else "#c62828",
        )
        if ok:
            self._sarf_tablo_guncelle()

    def _mali_rapor_goster(self):
        win = tk.Toplevel(self.root)
        win.title("Ay sonu mali raporu")
        win.minsize(560, 420)
        win.transient(self.root)
        cerceve = ttk.Frame(win, padding=10)
        cerceve.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(
            cerceve,
            wrap=tk.WORD,
            width=72,
            height=24,
            font=("Consolas", 10),
        )
        sb = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.insert(tk.END, mali_rapor_metni())
        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="Kapat", command=win.destroy).pack(pady=(0, 10))

    def _resmi_tablo_guncelle(self):
        for item in self.resmi_tree.get_children():
            self.resmi_tree.delete(item)
        for r in resmi_giderler:
            self.resmi_tree.insert(
                "",
                "end",
                values=(
                    r.get("tarih", ""),
                    r.get("kategori", ""),
                    f"{float(r.get('tutar', 0)):.2f}",
                    r.get("evrak_no", ""),
                ),
            )

    def _resmi_kayit_ekle(self):
        kat = self.resmi_kategori.get().strip()
        evrak = self.resmi_evrak.get().strip()
        if not kat:
            self.resmi_mesaj.config(
                text="Kategori girin.", foreground="#c62828"
            )
            return
        if not evrak:
            self.resmi_mesaj.config(
                text="Evrak numarası girin.", foreground="#c62828"
            )
            return
        ham = self.resmi_tutar.get().strip().replace(",", ".")
        try:
            tutar = float(ham)
        except ValueError:
            self.resmi_mesaj.config(
                text="Tutar geçerli bir sayı olmalı.", foreground="#c62828"
            )
            return
        if tutar <= 0:
            self.resmi_mesaj.config(
                text="Tutar sıfırdan büyük olmalı.", foreground="#c62828"
            )
            return
        resmi_gider_isle(kat, tutar, evrak, canlilar=self.canlilar, yazdir=False)
        self.resmi_kategori.delete(0, tk.END)
        self.resmi_tutar.delete(0, tk.END)
        self.resmi_evrak.delete(0, tk.END)
        self.resmi_mesaj.config(
            text="Resmi kayıt dosyalandı (database/petshop_defteri.json).",
            foreground="#2e7d32",
        )
        self._resmi_tablo_guncelle()

    def _kart_olustur(self, parent, c):
        f = ttk.LabelFrame(parent, text=f"{c.ad} — {c.tur}", padding=8)
        f.pack(fill=tk.X, pady=4)

        pb = ttk.Progressbar(f, length=400, mode="determinate", maximum=100)
        pb.pack(fill=tk.X, pady=4)

        bilgi = ttk.Label(f, text="")
        bilgi.pack(anchor=tk.W)

        porsiyon = ttk.Label(
            f,
            text=f"Her beslemede: {c.porsiyon_gram:g} g mama",
            foreground="#444",
        )
        porsiyon.pack(anchor=tk.W)

        btn = ttk.Button(f, text="Besle", command=lambda: self._besle(c))
        btn.pack(anchor=tk.E, pady=(6, 0))

        return {"canli": c, "pb": pb, "bilgi": bilgi}

    def _besle(self, c):
        c.besle()
        self._arayuzu_guncelle()
        kaydet(self.canlilar)

    def _tumunu_besle(self):
        for c in self.canlilar:
            c.besle()
        self._arayuzu_guncelle()
        kaydet(self.canlilar)

    @staticmethod
    def _jako_kusu():
        return next(k for k in kus_listesi if k.tur == "Jako Papağanı")

    def _stok_tablo_guncelle(self):
        for item in self.stok_tree.get_children():
            self.stok_tree.delete(item)
        for urun, miktar in stoklar.items():
            if miktar < STOCK_UYARI_ESIK:
                durum = "⚠️ Stok azalıyor!"
            else:
                durum = "✅ Tamam"
            self.stok_tree.insert(
                "",
                "end",
                values=(urun, f"{miktar:g}", durum),
            )

    def _stok_satis_yap(self):
        urun = self.stok_urun_combo.get()
        if not urun:
            self.stok_mesaj.config(
                text="Ürün seçin.", foreground="#c62828"
            )
            return
        ham = self.stok_miktar_entry.get().strip().replace(",", ".")
        try:
            miktar = float(ham)
        except ValueError:
            self.stok_mesaj.config(
                text="Miktar geçerli bir sayı olmalı.", foreground="#c62828"
            )
            return
        if miktar <= 0:
            self.stok_mesaj.config(
                text="Miktar sıfırdan büyük olmalı.", foreground="#c62828"
            )
            return
        ok, mesaj = satis_yap(urun, miktar)
        self.stok_mesaj.config(
            text=mesaj,
            foreground="#2e7d32" if ok else "#c62828",
        )
        if ok:
            kaydet(self.canlilar)
        self._stok_tablo_guncelle()

    def _aksesuar_tablo_guncelle(self):
        for item in self.aks_tree.get_children():
            self.aks_tree.delete(item)
        for urun, veri in aksesuarlar.items():
            st = veri["stok"]
            fy = veri["fiyat"]
            if st < AKSESUAR_STOK_UYARI_ESIK:
                durum = "⚠️ Stok azalıyor!"
            else:
                durum = "✅ Tamam"
            self.aks_tree.insert(
                "",
                "end",
                values=(urun, f"{st:g}", f"{fy:.2f}", durum),
            )

    def _aksesuar_stok_ekle_gui(self):
        urun = self.aks_stok_urun.get()
        if not urun:
            self.aks_mesaj.config(text="Ürün seçin.", foreground="#c62828")
            return
        ham = self.aks_stok_adet.get().strip().replace(",", ".")
        try:
            adet = float(ham)
        except ValueError:
            self.aks_mesaj.config(
                text="Adet geçerli bir sayı olmalı.", foreground="#c62828"
            )
            return
        if adet <= 0:
            self.aks_mesaj.config(
                text="Adet sıfırdan büyük olmalı.", foreground="#c62828"
            )
            return
        ok, mesaj = aksesuar_stok_ekle(urun, adet, yazdir=False)
        self.aks_mesaj.config(
            text=mesaj,
            foreground="#2e7d32" if ok else "#c62828",
        )
        if ok:
            kaydet(self.canlilar)
        self._aksesuar_tablo_guncelle()

    def _aksesuar_satis_gui(self):
        urun = self.aks_sat_urun.get()
        if not urun:
            self.aks_mesaj.config(text="Ürün seçin.", foreground="#c62828")
            return
        ham = self.aks_sat_adet.get().strip().replace(",", ".")
        try:
            adet = float(ham)
        except ValueError:
            self.aks_mesaj.config(
                text="Adet geçerli bir sayı olmalı.", foreground="#c62828"
            )
            return
        if adet <= 0:
            self.aks_mesaj.config(
                text="Adet sıfırdan büyük olmalı.", foreground="#c62828"
            )
            return
        ok, _, mesaj = aksesuar_satis(urun, adet, yazdir=False)
        self.aks_mesaj.config(
            text=mesaj,
            foreground="#2e7d32" if ok else "#c62828",
        )
        if ok:
            kaydet(self.canlilar)
        self._aksesuar_tablo_guncelle()

    def _finans_tablo_guncelle(self):
        for item in self.fin_tree.get_children():
            self.fin_tree.delete(item)
        for g in giderler:
            not_kisa = g["not"] if len(g["not"]) <= 80 else g["not"][:77] + "…"
            self.fin_tree.insert(
                "",
                "end",
                values=(g["kalem"], f"{g['miktar']:.2f}", not_kisa),
            )
        toplam = toplam_gider_hesapla(yazdir=False)
        self.fin_toplam.config(text=f"Toplam gider: {toplam:.2f} TL")
        if toplam > GIDER_UYARI_ESIK:
            self.fin_uyari.config(
                text="⚠️ DİKKAT: Giderler artıyor, kombiyi kapalı tutmaya devam kankam!",
                foreground="#ef6c00",
            )
        else:
            self.fin_uyari.config(text="")

    def _finans_gider_ekle(self):
        kalem = self.fin_kalem.get().strip()
        if not kalem:
            self.fin_mesaj.config(
                text="Kalem adı girin.", foreground="#c62828"
            )
            return
        ham = self.fin_miktar.get().strip().replace(",", ".")
        try:
            miktar = float(ham)
        except ValueError:
            self.fin_mesaj.config(
                text="Miktar geçerli bir sayı olmalı.", foreground="#c62828"
            )
            return
        if miktar <= 0:
            self.fin_mesaj.config(
                text="Miktar sıfırdan büyük olmalı.", foreground="#c62828"
            )
            return
        aciklama = self.fin_not.get("1.0", tk.END).strip()
        gider_ekle(kalem, miktar, aciklama, yazdir=False)
        kaydet(self.canlilar)
        self.fin_kalem.delete(0, tk.END)
        self.fin_miktar.delete(0, tk.END)
        self.fin_not.delete("1.0", tk.END)
        self.fin_mesaj.config(
            text="Gider kaydedildi.", foreground="#2e7d32"
        )
        self._finans_tablo_guncelle()

    def _jako_kelime_ogret(self):
        metin = self.jako_entry.get()
        self._jako_kusu().kelime_ogret(metin)
        m = (metin or "").strip()
        self.jako_entry.delete(0, tk.END)
        if m:
            kisa = m if len(m) <= 72 else m[:69] + "…"
            self.jako_durum.config(text=f"Profesör not etti: {kisa}")
        else:
            self.jako_durum.config(text="Boş metin kaydedilmedi — dürüst bir cümle yaz.")

    def _kuslari_dinle(self):
        self._kus_penceresi_ac(sabah_modu=False)

    def _kus_penceresi_ac(self, sabah_modu=False):
        win = tk.Toplevel(self.root)
        win.title("Sabah 07:00 — Neşe zamanı" if sabah_modu else "Kuş Cenneti")
        win.minsize(520, 360)
        win.transient(self.root)

        baslik_metni = (
            "☀️ Sabah 07:00 — Kuşlar ötüyor!  ·  Eski mesai saatin, şimdi neşe."
            if sabah_modu
            else "Pet Shop — Kuş Cenneti  ·  %100 Dürüstlük, %0 İsraf"
        )
        baslik = ttk.Label(win, text=baslik_metni, font=("Segoe UI", 10, "bold"))
        baslik.pack(anchor=tk.W, padx=10, pady=(10, 4))

        cerceve = ttk.Frame(win, padding=(10, 0, 10, 10))
        cerceve.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(
            cerceve,
            wrap=tk.WORD,
            width=72,
            height=18,
            font=("Segoe UI", 10),
            state=tk.NORMAL,
        )
        sb = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for kus in kus_listesi:
            txt.insert(tk.END, kus.ses_cikar() + "\n")
            txt.insert(tk.END, f"   > Özel yeteneği: {kus.yetenek}\n\n")
        txt.insert(
            tk.END,
            "Kankam, bak Jako bile 'Liyakat' diyor! Bu dükkanda kimse kimsenin hakkını yemez.",
        )
        txt.config(state=tk.DISABLED)

        ttk.Button(win, text="Kapat", command=win.destroy).pack(pady=(0, 10))

    def _sabah_zamanlayici_tick(self):
        simdi = datetime.now()
        bugun = date.today()
        if simdi.hour == SABAH_SAAT and simdi.minute == SABAH_DAKIKA:
            if self._son_sabah_otusu_tarihi != bugun:
                self._son_sabah_otusu_tarihi = bugun
                self._kus_penceresi_ac(sabah_modu=True)
        self._sabah_timer_id = self.root.after(SABAH_ZAMANLAYICI_MS, self._sabah_zamanlayici_tick)

    def _sabah_zamanlayici_baslat(self):
        if self._sabah_timer_id is not None:
            self.root.after_cancel(self._sabah_timer_id)
        self._sabah_timer_id = self.root.after(SABAH_ZAMANLAYICI_MS, self._sabah_zamanlayici_tick)

    def _arayuzu_guncelle(self):
        for k in self._kartlar:
            c = k["canli"]
            k["pb"].configure(value=c.tokluk_orani)
            k["bilgi"].config(
                text=f"Tokluk: %{c.tokluk_orani:.0f}  ·  Acılık: %{c.acilma_yuzdesi:.0f}"
            )

        for item in self.tree.get_children():
            self.tree.delete(item)

        genel = 0.0
        for c in self.canlilar:
            tutar = c.maliyet_tl()
            genel += tutar
            self.tree.insert(
                "",
                "end",
                values=(
                    c.ad,
                    c.tur,
                    f"{c.toplam_mama_gram:.1f}",
                    f"{MAMA_GRAM_BASINA_TL:.2f}",
                    f"{tutar:.2f}",
                ),
            )
        self.toplam_label.config(text=f"Genel toplam: {genel:.2f} TL  |  Toplam mama: {sum(x.toplam_mama_gram for x in self.canlilar):.1f} g")

    def _acilma_dongusu(self):
        for c in self.canlilar:
            c.acilma_adimi()
        self._arayuzu_guncelle()
        self._acilma_sayac += 1
        if self._acilma_sayac % ACILMA_KAYDET_ARALIK == 0:
            kaydet(self.canlilar)
        self._dongu_id = self.root.after(ACILMA_TICK_MS, self._acilma_dongusu)

    def _dongu_baslat(self):
        if self._dongu_id is not None:
            self.root.after_cancel(self._dongu_id)
        self._dongu_id = self.root.after(ACILMA_TICK_MS, self._acilma_dongusu)

    def on_close(self):
        kaydet(self.canlilar)
        if self._dongu_id is not None:
            self.root.after_cancel(self._dongu_id)
        if self._sabah_timer_id is not None:
            self.root.after_cancel(self._sabah_timer_id)
        self.root.destroy()


def main():
    magaza_acilis()
    root = tk.Tk()
    app = PetShopApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
