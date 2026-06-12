from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from app.config import APP_NAME
from app.db import Database
from app.ui.chat_window import ChatWindow


class LoginWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.db = Database()
        self.title(f"{APP_NAME} - Giriş")
        self.geometry("520x430")
        self.minsize(500, 420)

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Şifreli P2P Haberleşme",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(28, 8), sticky="ew")

        subtitle_text = (
            "İlk kullanımda kullanıcı oluşturun.\n"
            "Parola SHA-256 hash olarak yerel SQLite veritabanına kaydedilir."
        )
        subtitle = ctk.CTkLabel(self, text=subtitle_text, justify="center", wraplength=460)
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="ew")

        form = ctk.CTkFrame(self)
        form.grid(row=2, column=0, padx=28, pady=8, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)

        self.username_entry = ctk.CTkEntry(form, placeholder_text="Kullanıcı adı")
        self.username_entry.grid(row=0, column=0, padx=18, pady=(20, 10), sticky="ew")

        self.password_entry = ctk.CTkEntry(form, placeholder_text="Parola", show="*")
        self.password_entry.grid(row=1, column=0, padx=18, pady=10, sticky="ew")
        self.password_entry.bind("<Return>", lambda _event: self.login())

        login_btn = ctk.CTkButton(form, text="Giriş Yap", command=self.login)
        login_btn.grid(row=2, column=0, padx=18, pady=(16, 8), sticky="ew")

        register_btn = ctk.CTkButton(
            form,
            text="Yeni Kullanıcı Oluştur",
            fg_color="gray30",
            hover_color="gray25",
            command=self.register,
        )
        register_btn.grid(row=3, column=0, padx=18, pady=(0, 20), sticky="ew")

        hint = "Veritabanı: ./data/chat.db"
        if self.db.user_count() == 0:
            hint = "Henüz kullanıcı yok. Önce yeni kullanıcı oluşturun."
        self.info_label = ctk.CTkLabel(self, text=hint, text_color="gray75")
        self.info_label.grid(row=3, column=0, padx=24, pady=(18, 0), sticky="ew")

    def register(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if len(username) < 3:
            messagebox.showwarning("Eksik Bilgi", "Kullanıcı adı en az 3 karakter olmalı.")
            return
        if len(password) < 4:
            messagebox.showwarning("Eksik Bilgi", "Parola en az 4 karakter olmalı.")
            return
        if self.db.add_user(username, password):
            messagebox.showinfo("Başarılı", "Kullanıcı oluşturuldu. Şimdi giriş yapabilirsiniz.")
            self.info_label.configure(text="Kullanıcı oluşturuldu.")
        else:
            messagebox.showerror("Hata", "Bu kullanıcı adı zaten var veya bilgiler geçersiz.")

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if self.db.verify_user(username, password):
            self.withdraw()
            ChatWindow(master=self, username=username, db=self.db)
        else:
            messagebox.showerror("Giriş Başarısız", "Kullanıcı adı veya parola hatalı.")
