from __future__ import annotations

from typing import Any

import customtkinter as ctk
from tkinter import messagebox

from app.config import APP_NAME, DEFAULT_KEY, DEFAULT_PORT
from app.crypto import KeyExchange, Playfair6x6
from app.db import Database
from app.network import PeerNode
from app.utils import get_local_ip, get_tailscale_ip, now_iso


class ChatWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, username: str, db: Database) -> None:
        super().__init__(master)
        self.master_window = master
        self.username = username
        self.db = db

        self.peer_username = "Bağlantı yok"
        self.is_connector = False
        self.pending_session_key: str | None = None
        self.session_key: str | None = None
        self.key_exchange: KeyExchange | None = None
        self.session_cipher = None

        self.peer = PeerNode(
            on_message=self._on_network_message,
            on_status=self._on_network_status,
            on_error=self._on_network_error,
            on_connection=self._on_network_connection,
        )

        self.title(f"{APP_NAME} - {username}")
        self.geometry("1040x720")
        self.minsize(940, 660)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self._build_ui()
        self._load_history()

    # ---------- Arayüz ----------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkScrollableFrame(self, width=310, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_sidebar(sidebar)
        self._build_chat_area(main)

    def _build_sidebar(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Ağ ve Şifreleme", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=18, pady=(22, 10), sticky="w"
        )

        self.local_ip = get_local_ip()
        self.tailscale_ip = get_tailscale_ip()

        ctk.CTkLabel(parent, text=f"Yerel IP: {self.local_ip}").grid(
            row=1, column=0, padx=18, pady=(0, 4), sticky="w"
        )

        ctk.CTkLabel(parent, text=f"Tailscale IP: {self.tailscale_ip}").grid(
            row=2, column=0, padx=18, pady=(0, 14), sticky="w"
        )

        self._build_listen_box(parent, row=3)
        self._build_connect_box(parent, row=4)
        self._build_key_box(parent, row=5)
        self._build_status_box(parent, row=6)
        self._build_recent_chats_box(parent, row=7)
        self._build_help_box(parent,row=8)


    def _build_listen_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Dinleme Portu").grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        self.listen_port_entry = ctk.CTkEntry(box)
        self.listen_port_entry.insert(0, str(DEFAULT_PORT))
        self.listen_port_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkButton(box, text="Dinlemeyi Başlat", command=self.start_listening).grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

    def _build_connect_box(self, parent, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=18, pady=(0, 16), sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Bağlantı Türü").grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )

        self.connection_mode = ctk.CTkSegmentedButton(
            box,
            values=["Aynı Wi-Fi", "Farklı Wi-Fi / Tailscale"],
            command=self._on_connection_mode_changed,
        )
        self.connection_mode.set("Aynı Wi-Fi")
        self.connection_mode.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(box, text="Karşı Bilgisayar IP").grid(
            row=2, column=0, padx=12, pady=(4, 4), sticky="w"
        )

        self.peer_ip_entry = ctk.CTkEntry(
            box,
            placeholder_text="Örn: 192.168.1.25"
        )
        self.peer_ip_entry.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box, text="Karşı Port").grid(
            row=4, column=0, padx=12, pady=(4, 4), sticky="w"
        )

        self.peer_port_entry = ctk.CTkEntry(box)
        self.peer_port_entry.insert(0, str(DEFAULT_PORT))
        self.peer_port_entry.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            box,
            text="Bağlan",
            command=self.connect_to_peer
        ).grid(row=6, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(box, text="Bu mesajlaşmanın Playfair anahtarı").grid(
            row=7, column=0, padx=12, pady=(2, 4), sticky="w"
        )

        self.connect_key_entry = ctk.CTkEntry(
            box,
            show="*",
            placeholder_text="Bağlantıyı başlatan kişi belirler"
        )
        self.connect_key_entry.grid(row=8, column=0, padx=12, pady=(0, 8), sticky="ew")

        note = "Bu anahtar karşı tarafa açık gönderilmez; güvenli anahtar değişimi ile aktarılır."
        ctk.CTkLabel(
            box,
            text=note,
            justify="left",
            wraplength=255,
            text_color="gray70"
        ).grid(row=9, column=0, padx=12, pady=(0, 12), sticky="w")

    def _build_key_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Oturum Anahtarı").grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        self.session_label = ctk.CTkLabel(box, text="Anahtar: bekleniyor", text_color="gray75")
        self.session_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        ctk.CTkButton(
            box,
            text="Oturum Anahtarını Göster",
            fg_color="gray30",
            hover_color="gray25",
            command=self.show_session_key,
        ).grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            box,
            text="6x6 Matrisi Göster",
            fg_color="gray30",
            hover_color="gray25",
            command=self.show_matrix,
        ).grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _build_status_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(box, text="●", text_color="red", font=ctk.CTkFont(size=18))
        self.status_dot.grid(row=0, column=0, padx=(12, 4), pady=12)

        self.status_label = ctk.CTkLabel(box, text="Bağlantı yok", wraplength=220, justify="left")
        self.status_label.grid(row=0, column=1, padx=(4, 12), pady=12, sticky="w")

    def _build_chat_area(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.chat_title_label = ctk.CTkLabel(header, text="Şifreli Sohbet", font=ctk.CTkFont(size=22, weight="bold"))
        self.chat_title_label.grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")

        self.peer_name_label = ctk.CTkLabel(header, text="Kiminle: Bağlantı yok", text_color="gray75")
        self.peer_name_label.grid(row=1, column=0, padx=14, pady=(0, 4), sticky="w")

        self.message_hint_label = ctk.CTkLabel(
            header,
            text="Mesajlar önce şifreli görünür. Açık halini görmek için mesaja tıkla.",
            text_color="gray75",
        )
        self.message_hint_label.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        ctk.CTkLabel(header, text=f"Oturum: {self.username}", text_color="gray75").grid(
            row=0, column=1, rowspan=3, padx=14, pady=12, sticky="e"
        )

        self.chat_area = ctk.CTkScrollableFrame(parent)
        self.chat_area.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="nsew")
        self.chat_area.grid_columnconfigure(0, weight=1)
        self._message_row = 0

        send_frame = ctk.CTkFrame(parent)
        send_frame.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="ew")
        send_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(
            send_frame,
            placeholder_text="Mesaj yazın... boşluk, nokta, virgül ve Türkçe karakterler desteklenir",
        )
        self.message_entry.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
        self.message_entry.bind("<Return>", lambda _event: self.send_message())

        ctk.CTkButton(send_frame, text="Gönder", width=110, command=self.send_message).grid(
            row=0, column=1, padx=(8, 12), pady=12
        )

    def _build_recent_chats_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text="Son Konuşmalar",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.recent_chats_frame = ctk.CTkScrollableFrame(box, height=130)
        self.recent_chats_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
        self.recent_chats_frame.grid_columnconfigure(0, weight=1)

        self._load_recent_chats()

    def _build_help_box(self, parent, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text="Kullanım",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        help_text = (
            "1) İki bilgisayarda da dinlemeyi başlatın.\n"
            "2) Bağlanan taraf Playfair anahtarını belirler.\n"
            "3) Anahtar güvenli şekilde aktarılır.\n"
            "4) Mesajlar ağda şifreli gider.\n"
            "5) Mesaja tıklayarak açık metni görebilirsiniz."
        )

        ctk.CTkLabel(
            box,
            text=help_text,
            justify="left",
            wraplength=250,
            text_color="gray70"
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")

    def _load_recent_chats(self) -> None:
        for widget in self.recent_chats_frame.winfo_children():
            widget.destroy()

        rows = self.db.get_recent_peers(self.username)

        if not rows:
            ctk.CTkLabel(
                self.recent_chats_frame,
                text="Henüz kayıtlı konuşma yok.",
                text_color="gray70"
            ).grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for index, row in enumerate(rows):
            peer_address = row["peer_address"]
            display_name = row["display_name"]
            message_count = row["message_count"]

            text = f"{display_name}  •  {message_count} mesaj"

            row_frame = ctk.CTkFrame(self.recent_chats_frame, fg_color="transparent")
            row_frame.grid(row=index, column=0, padx=4, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkButton(
                row_frame,
                text=text,
                anchor="w",
                fg_color="gray25",
                hover_color="gray35",
                command=lambda address=peer_address: self._ask_password_and_open_history(address),
            ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

            ctk.CTkButton(
                row_frame,
                text="🗑",
                width=36,
                fg_color="gray25",
                hover_color="red",
                command=lambda address=peer_address: self._delete_recent_chat(address),
            ).grid(row=0, column=1, sticky="e")

    def _delete_recent_chat(self, peer_address: str) -> None:
        answer = messagebox.askyesno(
            "Sohbeti Sil",
            "Bu kişiyle olan sohbet geçmişini silmek istiyor musunuz?"
        )

        if not answer:
            return

        self.db.delete_messages_with_peer(self.username, peer_address)
        self._load_recent_chats()

    def _ask_password_and_open_history(self, peer_address: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("Sohbet Geçmişi")
        popup.geometry("360x180")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text="Sohbet geçmişini görüntülemek için\nkullanıcı şifrenizi girin.",
            justify="center"
        ).pack(pady=(20, 10))

        password_entry = ctk.CTkEntry(popup, show="*")
        password_entry.pack(padx=24, pady=8, fill="x")

        def check_password() -> None:
            password = password_entry.get()

            if not self.db.verify_user(self.username, password):
                messagebox.showerror("Hatalı Şifre", "Kullanıcı şifresi yanlış.")
                return

            popup.destroy()
            self._open_chat_from_recent(peer_address)

        ctk.CTkButton(
            popup,
            text="Geçmişi Aç",
            command=check_password
        ).pack(pady=12)

        password_entry.bind("<Return>", lambda _event: check_password())


    def _open_chat_history(self, peer_address: str) -> None:
        rows = self.db.get_messages_with_peer(self.username, peer_address, limit=100)

        history_window = ctk.CTkToplevel(self)
        history_window.title(f"Son Konuşmalar - {peer_address}")
        history_window.geometry("720x520")
        history_window.grid_columnconfigure(0, weight=1)
        history_window.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            history_window,
            text=f"Sohbet Geçmişi: {peer_address}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        frame = ctk.CTkScrollableFrame(history_window)
        frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        if not rows:
            ctk.CTkLabel(
                frame,
                text="Bu kişiyle kayıtlı mesaj bulunamadı.",
                text_color="gray70"
            ).grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for index, row in enumerate(rows):
            direction = "Ben" if row["direction"] == "OUT" else "Karşı taraf"
            text = (
                f"{direction} • {row['created_at']}\n\n"
                f"Şifreli:\n{row['ciphertext']}\n\n"
                f"Açık Metin:\n{row['plaintext']}"
            )

            ctk.CTkLabel(
                frame,
                text=text,
                justify="left",
                anchor="w",
                wraplength=640,
                fg_color=("gray85", "gray25"),
                corner_radius=10
            ).grid(row=index, column=0, padx=8, pady=8, sticky="ew")

    def _open_chat_from_recent(self, peer_address: str) -> None:
        rows = self.db.get_messages_with_peer(self.username, peer_address, limit=100)

        # Sohbet ekranını temizle
        for widget in self.chat_area.winfo_children():
            widget.destroy()

        self._message_row = 0

        # Başlığı güncelle
        self.peer_username = peer_address
        self._refresh_peer_header()

        if not rows:
            self._add_system_message("Bu konuşmaya ait kayıtlı mesaj bulunamadı.")
            return

        self._add_system_message("Seçilen sohbet geçmişi yüklendi.")

        for row in rows:
            direction = row["direction"]
            outgoing = direction == "OUT"

            if outgoing:
                sender_name = "Ben"
            else:
                try:
                    sender_name = row["peer_username"] or "Karşı taraf"
                except Exception:
                    sender_name = "Karşı taraf"

            self._add_message_bubble(
                sender_name,
                row["ciphertext"],
                row["plaintext"],
                outgoing=outgoing,
            )

    def _on_connection_mode_changed(self, mode: str) -> None:
        if mode == "Aynı Wi-Fi":
            self.peer_ip_entry.configure(
                placeholder_text="Örn: 192.168.1.25"
            )
            message = (
                f"Aynı Wi-Fi modu seçildi. "
                f"Karşı cihaz bu ağa bağlıysa onun Yerel IP adresini girin. "
                f"Senin Yerel IP: {self.local_ip}"
            )
        else:
            self.peer_ip_entry.configure(
                placeholder_text="Örn: 100.x.x.x Tailscale IP"
            )
            message = (
                f"Tailscale modu seçildi. "
                f"Karşı cihazın Tailscale IP adresini girin. "
                f"Senin Tailscale IP: {self.tailscale_ip}"
            )

        if hasattr(self, "status_label"):
            self._set_status(message, connected=self.peer.connected)


    # ---------- Kullanıcı işlemleri ----------

    def start_listening(self) -> None:
        port = self._read_port(self.listen_port_entry, "Dinleme portu")
        if port is not None:
            self.peer.start_server(port)

    def connect_to_peer(self) -> None:
        host = self.peer_ip_entry.get().strip()

        if not host:
            messagebox.showwarning("Eksik Bilgi", "Karşı bilgisayarın IP adresini yazın.")
            return

        mode = self.connection_mode.get()

        if mode == "Farklı Wi-Fi / Tailscale" and not host.startswith("100."):
            self._set_status(
                "Tailscale modu seçili. Karşı cihazın 100.x.x.x ile başlayan Tailscale IP adresini girin.",
                connected=False,
            )
            return

        if mode == "Aynı Wi-Fi" and host.startswith("100."):
            self._set_status(
                "Aynı Wi-Fi modu seçili. 100.x.x.x Tailscale IP yerine yerel 192.168.x.x IP girmeniz beklenir.",
                connected=False,
            )
            return

        port = self._read_port(self.peer_port_entry, "Karşı port")
        if port is None:
            return

        selected_key = self._read_connection_key()
        if selected_key is None:
            return

        self.pending_session_key = selected_key
        self.is_connector = True
        self.peer.connect(host, port)

    def send_message(self) -> None:
        if self.peer.connected and self.session_key is None:
            messagebox.showwarning("Anahtar Bekleniyor", "Güvenli oturum anahtarı henüz kurulmadı.")
            return

        raw_message = self.message_entry.get()
        if not raw_message.strip():
            return

        cipher = self._playfair()
        plaintext = cipher.normalize(raw_message)
        if not plaintext.strip():
            messagebox.showwarning("Mesaj Gönderilemedi", "Mesaj desteklenen karakterlerden en az birini içermeli.")
            return

        ciphertext = cipher.encrypt(plaintext)
        payload = {"type": "message", "sender": self.username, "ciphertext": ciphertext, "timestamp": now_iso()}

        if self.peer.send_payload(payload):
            self.db.save_message(self.username, self.peer.peer_address, "OUT", plaintext, ciphertext, self.peer_username)
            self._add_message_bubble("Ben", ciphertext, plaintext, outgoing=True)
            self._load_recent_chats()
            self.message_entry.delete(0, "end")

    def show_session_key(self) -> None:
        if self.session_key is None:
            messagebox.showinfo("Oturum Anahtarı", "Henüz güvenli oturum anahtarı kurulmadı.")
            return
        messagebox.showinfo("Oturum Playfair Anahtarı", self.session_key)

    def show_matrix(self) -> None:
        if self.session_key is None:
            messagebox.showinfo("6x6 Türkçe Playfair Matrisi", "Önce güvenli oturum anahtarı kurulmalı.")
            return
        messagebox.showinfo("6x6 Türkçe Playfair Matrisi", self._playfair().matrix_as_text())

    # ---------- Ağ mesajları ----------

    def _on_network_connection(self, addr: tuple[str, int]) -> None:
        self.after(0, lambda: self._handle_connection_change(addr))

    def _handle_connection_change(self, addr: tuple[str, int]) -> None:
        if addr == ("", 0):
            self._reset_session()
            self.peer_username = "Bağlantı yok"
            self._set_status("Bağlantı yok", connected=False)
            self._refresh_peer_header()
            return

        self.peer_username = f"{addr[0]}:{addr[1]}"
        self._set_status(f"Bağlı: {self.peer_username}", connected=True)
        self._refresh_peer_header()
        self._send_hello()

        if self.is_connector:
            self._start_key_exchange()
        else:
            self._set_session_status("Anahtar: karşı taraftan bekleniyor")

    def _send_hello(self) -> None:
        self.peer.send_payload({"type": "hello", "sender": self.username, "timestamp": now_iso()})

    def _start_key_exchange(self) -> None:
        self.key_exchange = KeyExchange.create()
        self.peer.send_payload({
            "type": "key_public",
            "sender": self.username,
            "public_key": self.key_exchange.public_key_text(),
            "timestamp": now_iso(),
        })
        self._set_session_status("Anahtar: Diffie-Hellman değişimi başlatıldı")

    def _on_network_message(self, payload: dict[str, Any], addr: tuple[str, int]) -> None:
        self.after(0, lambda: self._handle_network_message(payload, addr))

    def _handle_network_message(self, payload: dict[str, Any], addr: tuple[str, int]) -> None:
        message_type = payload.get("type")

        if message_type == "hello":
            self._update_peer_name(str(payload.get("sender", "Karşı taraf")))
        elif message_type == "key_public":
            self._receive_public_key(payload)
        elif message_type == "key_public_reply":
            self._receive_public_key_reply(payload)
        elif message_type == "session_key":
            self._receive_session_key(payload)
        elif message_type == "message":
            self._receive_chat_message(payload, addr)

    def _receive_public_key(self, payload: dict[str, Any]) -> None:
        """Dinleyen taraf, bağlanan tarafın public key bilgisini alır ve kendi public key bilgisini döner."""
        try:
            self.key_exchange = KeyExchange.create()
            self.session_cipher = self.key_exchange.build_cipher(str(payload["public_key"]))
            self.peer.send_payload({
                "type": "key_public_reply",
                "sender": self.username,
                "public_key": self.key_exchange.public_key_text(),
                "timestamp": now_iso(),
            })
            self._set_session_status("Anahtar: şifreli Playfair anahtarı bekleniyor")
        except Exception as exc:
            self._set_status(f"Anahtar değişimi hatası: {exc}", connected=True, error=True)

    def _receive_public_key_reply(self, payload: dict[str, Any]) -> None:
        """Bağlanan taraf, seçtiği Playfair anahtarını güvenli kanalda şifreleyerek gönderir."""
        try:
            if self.key_exchange is None:
                raise ValueError("Anahtar değişimi başlatılmadı.")
            if self.pending_session_key is None:
                raise ValueError("Playfair anahtarı seçilmedi.")

            self.session_cipher = self.key_exchange.build_cipher(str(payload["public_key"]))
            encrypted_key = self.session_cipher.encrypt(self.pending_session_key.encode("utf-8")).decode("ascii")

            self._set_session_key(self.pending_session_key)
            self.peer.send_payload({
                "type": "session_key",
                "sender": self.username,
                "encrypted_key": encrypted_key,
                "timestamp": now_iso(),
            })
            self._add_system_message("Playfair anahtarı Diffie-Hellman sonrası şifreli olarak karşı tarafa gönderildi.")
        except Exception as exc:
            self._set_status(f"Anahtar gönderme hatası: {exc}", connected=True, error=True)

    def _receive_session_key(self, payload: dict[str, Any]) -> None:
        """Dinleyen taraf, şifreli gelen Playfair anahtarını çözer."""
        try:
            if self.session_cipher is None:
                raise ValueError("Ortak gizli anahtar henüz oluşmadı.")

            encrypted_key = str(payload["encrypted_key"]).encode("ascii")
            session_key = self.session_cipher.decrypt(encrypted_key).decode("utf-8")
            self._set_session_key(session_key)
            self._add_system_message("Playfair oturum anahtarı güvenli şekilde alındı. Mesajlaşma hazır.")
            self.after(100, self._show_session_key_received_popup)
        except Exception as exc:
            self._set_status(f"Oturum anahtarı çözülemedi: {exc}", connected=True, error=True)

    def _show_session_key_received_popup(self) -> None:
        answer = messagebox.askyesno(
            "Oturum Anahtarı Alındı",
            "Güvenli oturum anahtarı alındı.\n\nAnahtarı görüntülemek ister misiniz?"
        )

        if answer:
            self.show_session_key()

    def _receive_chat_message(self, payload: dict[str, Any], addr: tuple[str, int]) -> None:
        if self.session_key is None:
            self._set_status("Mesaj geldi ama oturum anahtarı hazır değil.", connected=True, error=True)
            return

        sender = str(payload.get("sender", "Karşı taraf"))
        ciphertext = str(payload.get("ciphertext", ""))

        try:
            plaintext = self._playfair().decrypt(ciphertext)
        except Exception as exc:
            self._set_status(f"Çözme hatası: {exc}", connected=self.peer.connected, error=True)
            return

        self._update_peer_name(sender)
        peer_address = f"{addr[0]}:{addr[1]}"
        self.db.save_message(self.username, peer_address, "IN", plaintext, ciphertext, sender)
        self._add_message_bubble(sender, ciphertext, plaintext, outgoing=False)
        self._load_recent_chats()

    def _on_network_status(self, text: str) -> None:
        self.after(0, lambda: self._set_status(text, connected=self.peer.connected))

    def _on_network_error(self, text: str) -> None:
        self.after(0, lambda: self._set_status(text, connected=self.peer.connected, error=True))

    # ---------- Yardımcı metotlar ----------

    def _playfair(self) -> Playfair6x6:
        return Playfair6x6(self.session_key or DEFAULT_KEY)

    def _read_connection_key(self) -> str | None:
        raw_key = self.connect_key_entry.get()
        normalized_key = Playfair6x6(raw_key).normalize(raw_key)

        if not normalized_key.strip():
            messagebox.showwarning(
                "Anahtar Hatası",
                "Playfair anahtarı en az bir desteklenen karakter içermeli. Türkçe harf, boşluk, . , ? ! : kullanabilirsiniz.",
            )
            return None

        return normalized_key

    def _set_session_key(self, key: str) -> None:
        self.session_key = key
        self._set_session_status("Anahtar: güvenli oturum hazır")
        self._set_status("Güvenli bağlantı hazır", connected=True)

    def _reset_session(self) -> None:
        self.is_connector = False
        self.pending_session_key = None
        self.session_key = None
        self.key_exchange = None
        self.session_cipher = None
        self._set_session_status("Anahtar: bekleniyor")

    def _set_session_status(self, text: str) -> None:
        self.session_label.configure(text=text)

    def _read_port(self, entry: ctk.CTkEntry, label: str) -> int | None:
        try:
            port = int(entry.get().strip())
            if 1 <= port <= 65535:
                return port
        except ValueError:
            pass

        messagebox.showwarning("Port Hatası", f"{label} 1-65535 arasında sayı olmalıdır.")
        return None

    def _update_peer_name(self, name: str) -> None:
        if name.strip():
            self.peer_username = name.strip()
            self._refresh_peer_header()

    def _refresh_peer_header(self) -> None:
        self.peer_name_label.configure(text=f"Kiminle: {self.peer_username}")

    def _set_status(self, text: str, connected: bool, error: bool = False) -> None:
        self.status_label.configure(text=text)
        if error:
            self.status_dot.configure(text_color="orange")
        elif connected:
            self.status_dot.configure(text_color="lime")
        else:
            self.status_dot.configure(text_color="red")

    def _load_history(self) -> None:
        rows = self.db.get_recent_messages(self.username, limit=20)
        if not rows:
            self._add_system_message("Sohbet geçmişi boş. Dinlemeyi başlatıp karşı bilgisayara bağlanabilirsiniz.")
            return

        self._add_system_message("Son mesaj geçmişi yüklendi. Geçmiş mesajlar da önce şifreli görünür.")
        for row in rows:
            sender = "Ben" if row["direction"] == "OUT" else "Karşı taraf"
            sender = f"{sender} ({row['created_at']})"
            self._add_message_bubble(sender, row["ciphertext"], row["plaintext"], outgoing=row["direction"] == "OUT")

    def _add_system_message(self, text: str) -> None:
        label = ctk.CTkLabel(self.chat_area, text=text, text_color="gray70", justify="center")
        label.grid(row=self._message_row, column=0, padx=12, pady=6, sticky="ew")
        self._message_row += 1

    def _add_message_bubble(self, sender: str, ciphertext: str, plaintext: str, outgoing: bool) -> None:
        # Mesaj balonunda sadece mesaj içeriği görünür.
        # İlk durumda şifreli metin, tıklandıktan sonra açık metin gösterilir.
        encrypted_text = ciphertext
        decrypted_text = plaintext

        bubble = ctk.CTkLabel(
            self.chat_area,
            text=encrypted_text,
            justify="left",
            anchor="w",
            wraplength=600,
            fg_color=("gray85", "gray25") if not outgoing else ("#D7ECFF", "#1F4E79"),
            corner_radius=12,
        )
        bubble.grid(
            row=self._message_row,
            column=0,
            padx=(90, 12) if outgoing else (12, 90),
            pady=6,
            sticky="e" if outgoing else "w",
        )
        bubble.bind("<Button-1>", lambda _event: self._decrypt_bubble(bubble, decrypted_text))
        self._message_row += 1

    def _decrypt_bubble(self, bubble: ctk.CTkLabel, decrypted_text: str) -> None:
        bubble.configure(text=decrypted_text)
        bubble.unbind("<Button-1>")

    def close_app(self) -> None:
        self.peer.stop()
        self.db.close()
        self.destroy()
        self.master_window.destroy()
