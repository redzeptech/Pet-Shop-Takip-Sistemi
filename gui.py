"""Modern dashboard arayuzu (CustomTkinter).

Calistirma:
    python gui.py
"""
from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from modules.aksesuar import AKSESUAR_STOK_UYARI_ESIK, aksesuarlar
from modules.defter import kaydet, magaza_acilis
from modules.stok import STOCK_UYARI_ESIK, stoklar

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FORBIDDEN_WORDS = ("kedi", "kopek", "köpek", "dog", "cat", "yavru")


def _is_forbidden_sale(item_name: str, category: str) -> bool:
    lowered = (item_name or "").strip().lower()
    return category == "Ürün" and any(word in lowered for word in FORBIDDEN_WORDS)


def process_transaction(item_name: str, category: str, amount: float) -> tuple[bool, str]:
    item = (item_name or "").strip()
    if not item:
        return False, "İşlem/ürün adı boş olamaz."
    if category not in ("Ürün", "Hizmet"):
        return False, "Kategori yalnızca Ürün veya Hizmet olabilir."
    if _is_forbidden_sale(item, category):
        return False, "Hata: Canlı hayvan satışı bu işletmede yasaktır!"
    if amount <= 0:
        return False, "Tutar sıfırdan büyük olmalıdır."

    if category == "Ürün":
        if item in stoklar:
            if stoklar[item] < 1:
                return False, "Yetersiz stok."
            stoklar[item] -= 1
        elif item in aksesuarlar:
            if aksesuarlar[item]["stok"] < 1:
                return False, "Yetersiz stok."
            aksesuarlar[item]["stok"] -= 1
        else:
            return False, "Ürün stok listesinde bulunamadı."

    kaydet()
    return True, "İşlem başarıyla kasaya işlendi."


class PetShopDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        magaza_acilis()

        self.title("Pet Shop Takip Sistemi - Modern Panel")
        self.geometry("1100x680")
        self.minsize(920, 560)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_content = ctk.CTkFrame(self, corner_radius=12)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=14, pady=14)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(self.sidebar, text="PET SHOP", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(20, 4)
        )
        ctk.CTkLabel(self.sidebar, text="Dashboard", text_color="gray70").grid(
            row=1, column=0, padx=16, pady=(0, 10)
        )
        ctk.CTkButton(self.sidebar, text="Stok", command=self.show_stock, anchor="w").grid(
            row=2, column=0, padx=14, pady=6, sticky="ew"
        )
        ctk.CTkButton(self.sidebar, text="Raporlar", command=self.show_reports, anchor="w").grid(
            row=3, column=0, padx=14, pady=6, sticky="ew"
        )
        ctk.CTkButton(self.sidebar, text="Hızlı Kasa", command=self.open_sales_window, anchor="w").grid(
            row=4, column=0, padx=14, pady=6, sticky="ew"
        )
        ctk.CTkButton(self.sidebar, text="Etik Beyan", command=self.show_ethics_declaration, anchor="w").grid(
            row=5, column=0, padx=14, pady=6, sticky="ew"
        )

        self.stock_tree: ttk.Treeview | None = None
        self.report_tree: ttk.Treeview | None = None
        self.lbl_daily_amount: ctk.CTkLabel | None = None
        self.lbl_service_amount: ctk.CTkLabel | None = None

        self.sales_win: ctk.CTkToplevel | None = None
        self.transaction_type: ctk.CTkSegmentedButton | None = None
        self.entry_item: ctk.CTkEntry | None = None
        self.entry_amount: ctk.CTkEntry | None = None
        self.sales_status: ctk.CTkLabel | None = None

        self.sales_records: list[dict[str, object]] = []
        self.show_reports()

    def clear_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_stock(self):
        self.clear_content()
        ctk.CTkLabel(self.main_content, text="Stok ve Ürün Yönetimi", font=("Arial", 22, "bold")).pack(pady=10)

        columns = ("urun", "kategori", "stok", "durum")
        self.stock_tree = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col, text in (("urun", "Ürün"), ("kategori", "Kategori"), ("stok", "Stok"), ("durum", "Durum")):
            self.stock_tree.heading(col, text=text)
        self.stock_tree.tag_configure("low_stock", background="#8B0000", foreground="white")
        self.stock_tree.tag_configure("normal_stock", background="#2b2b2b")
        self.stock_tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.refresh_stock_table()

    def refresh_stock_table(self):
        if self.stock_tree is None:
            return
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        for urun, miktar in stoklar.items():
            low = float(miktar) <= float(STOCK_UYARI_ESIK)
            self.stock_tree.insert(
                "", "end", values=(urun, "Ürün", f"{miktar:g}", "Kritik" if low else "Normal"), tags=("low_stock" if low else "normal_stock",)
            )
        for urun, detay in aksesuarlar.items():
            st = float(detay.get("stok", 0))
            low = st <= float(AKSESUAR_STOK_UYARI_ESIK)
            self.stock_tree.insert(
                "", "end", values=(urun, "Ürün", f"{st:g}", "Kritik" if low else "Normal"), tags=("low_stock" if low else "normal_stock",)
            )

    def show_reports(self):
        self.clear_content()
        ctk.CTkLabel(self.main_content, text="Bugün Ne Kazandık?", font=("Arial", 22, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 8)
        )

        stats = ctk.CTkFrame(self.main_content, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="w", padx=12)
        daily = ctk.CTkFrame(stats, width=260, height=110, fg_color="#1f538d")
        daily.grid(row=0, column=0, padx=(0, 10))
        daily.grid_propagate(False)
        ctk.CTkLabel(daily, text="Bugünkü Toplam Ciro").pack(pady=(12, 6))
        self.lbl_daily_amount = ctk.CTkLabel(daily, text="0.00 TL", font=("Arial", 22, "bold"))
        self.lbl_daily_amount.pack()

        service = ctk.CTkFrame(stats, width=260, height=110, fg_color="#28a745")
        service.grid(row=0, column=1)
        service.grid_propagate(False)
        ctk.CTkLabel(service, text="Hizmet Gelirleri").pack(pady=(12, 6))
        self.lbl_service_amount = ctk.CTkLabel(service, text="0.00 TL", font=("Arial", 22, "bold"))
        self.lbl_service_amount.pack()

        ctk.CTkLabel(self.main_content, text="Son İşlemler", font=("Arial", 18, "bold")).grid(
            row=2, column=0, sticky="w", padx=12, pady=(8, 4)
        )
        wrap = ctk.CTkFrame(self.main_content, fg_color="transparent")
        wrap.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.main_content.grid_rowconfigure(3, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        columns = ("tarih", "islem", "kategori", "tutar")
        self.report_tree = ttk.Treeview(wrap, columns=columns, show="headings")
        self.report_tree.heading("tarih", text="Tarih")
        self.report_tree.heading("islem", text="İşlem/Ürün")
        self.report_tree.heading("kategori", text="Kategori")
        self.report_tree.heading("tutar", text="Tutar (TL)")
        self.report_tree.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.report_tree.yview).grid(row=0, column=1, sticky="ns")
        self.update_report_stats()

    def update_report_stats(self):
        today = datetime.now().date()
        daily = 0.0
        service = 0.0
        if self.report_tree is not None:
            for item in self.report_tree.get_children():
                self.report_tree.delete(item)

        for rec in reversed(self.sales_records[-200:]):
            dt = rec["sale_date"]
            amount = float(rec["amount"])
            category = str(rec["category"])
            if dt.date() == today:
                daily += amount
                if category == "Hizmet":
                    service += amount
            if self.report_tree is not None:
                self.report_tree.insert(
                    "",
                    "end",
                    values=(dt.strftime("%Y-%m-%d %H:%M"), rec["item_name"], category, f"{amount:.2f}"),
                )

        if self.lbl_daily_amount is not None:
            self.lbl_daily_amount.configure(text=f"{daily:.2f} TL")
        if self.lbl_service_amount is not None:
            self.lbl_service_amount.configure(text=f"{service:.2f} TL")

    def open_sales_window(self):
        if self.sales_win is not None and self.sales_win.winfo_exists():
            self.sales_win.focus()
            return
        self.sales_win = ctk.CTkToplevel(self)
        self.sales_win.title("Yeni İşlem / Kasa")
        self.sales_win.geometry("400x520")
        self.sales_win.attributes("-topmost", True)

        ctk.CTkLabel(self.sales_win, text="Hızlı Kasa İşlemi", font=("Arial", 20, "bold")).pack(pady=20)
        self.transaction_type = ctk.CTkSegmentedButton(self.sales_win, values=["Ürün Satışı", "Hizmet Bedeli"])
        self.transaction_type.set("Ürün Satışı")
        self.transaction_type.pack(pady=10)
        self.entry_item = ctk.CTkEntry(self.sales_win, placeholder_text="İşlem/Ürün Adı", width=300)
        self.entry_item.pack(pady=15)
        self.entry_amount = ctk.CTkEntry(self.sales_win, placeholder_text="Tutar (TL)", width=300)
        self.entry_amount.pack(pady=15)
        ctk.CTkButton(
            self.sales_win,
            text="Kasaya İşle",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.complete_sale,
        ).pack(pady=20)
        self.sales_status = ctk.CTkLabel(self.sales_win, text="", text_color="gray70")
        self.sales_status.pack()

    def complete_sale(self):
        if self.transaction_type is None or self.entry_item is None or self.entry_amount is None:
            return
        item = self.entry_item.get().strip()
        cat = "Ürün" if self.transaction_type.get() == "Ürün Satışı" else "Hizmet"
        try:
            amount = float(self.entry_amount.get().strip().replace(",", "."))
        except ValueError:
            if self.sales_status is not None:
                self.sales_status.configure(text="UYARI: Tutar sayısal olmalıdır.", text_color="#ff6b6b")
            return

        ok, msg = process_transaction(item, cat, amount)
        if not ok:
            if self.sales_status is not None:
                self.sales_status.configure(text=f"UYARI: {msg}", text_color="#ff6b6b")
            return

        self.sales_records.append(
            {
                "item_name": item,
                "category": cat,
                "amount": amount,
                "sale_date": datetime.now(),
            }
        )
        if self.sales_win is not None and self.sales_win.winfo_exists():
            self.sales_win.destroy()
            self.sales_win = None
        self.show_reports()
        messagebox.showinfo("Kasa", msg)

    def show_ethics_declaration(self):
        ethics_win = ctk.CTkToplevel(self)
        ethics_win.title("Hayvan Hakları ve Etik Beyanı")
        ethics_win.geometry("700x620")
        ethics_win.attributes("-topmost", True)
        ctk.CTkLabel(
            ethics_win,
            text="PET SHOP TAKİP SİSTEMİ: HAYVAN HAKLARI VE ETİK ÇALIŞMA BEYANI",
            font=("Arial", 16, "bold"),
            wraplength=650,
            justify="left",
        ).pack(pady=(16, 8), padx=20, anchor="w")
        t = ctk.CTkTextbox(ethics_win, width=650, height=470, font=("Arial", 13))
        t.pack(pady=10, padx=20, fill="both", expand=True)
        t.insert(
            "0.0",
            (
                "1) Canlılık Onuru: Hayvanlar ticari meta değildir.\n\n"
                "2) Satış Yasağı: Kedi, köpek ve memeli canlıların ücretli satışı yasaktır.\n\n"
                "3) Nesneleştirme Karşıtlığı: Hayvanlar oyuncak değildir.\n\n"
                "4) Çocuk ve Hayvan İlişkisi: Saygı ve sınır bilinci esastır.\n\n"
                "5) Hukuki Dayanak: 5199 sayılı Kanun ve evrensel etik ilkeler."
            ),
        )
        t.configure(state="disabled")
        ctk.CTkButton(ethics_win, text="Okudum, Anladım ve Kabul Ediyorum", command=ethics_win.destroy).pack(
            pady=(8, 14)
        )


if __name__ == "__main__":
    app = PetShopDashboard()
    app.mainloop()
