from __future__ import annotations

from typing import Any

import customtkinter as ctk
from tkinter import messagebox

from app.config import APP_NAME, DEFAULT_KEY, DEFAULT_PORT
from app.crypto import Playfair6x6
from app.db import Database
from app.network import PeerNode
from app.utils import get_local_ip, now_iso


class ChatWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, username: str, db: Database) -> None:
        super().__init__(master)
        self.master_window = master
        self.username = username
        self.db = db
        self.peer_username = "Bağlantı yok"

        self.peer = PeerNode(
            on_message=self._on_network_message,
            on_status=self._on_network_status,
            on_error=self._on_network_error,
            on_connection=self._on_network_connection,
        )

        self.title(f"{APP_NAME} - {username}")
        self.geometry("1020x700")
        self.minsize(920, 640)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self._build_ui()
        self._load_history()

    # ---------- Arayüz ----------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_sidebar(sidebar)
        self._build_chat_area(main)

    def _build_sidebar(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent,
            text="Ağ ve Şifreleme",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(22, 10), sticky="w")

        self.local_ip = get_local_ip()
        ctk.CTkLabel(parent, text=f"Yerel IP: {self.local_ip}").grid(
            row=1, column=0, padx=18, pady=(0, 14), sticky="w"
        )

        self._build_listen_box(parent, row=2)
        self._build_connect_box(parent, row=3)
        self._build_key_box(parent, row=4)
        self._build_status_box(parent, row=5)

        help_text = (
            "Kullanım:\n"
            "1) İki bilgisayarda da dinlemeyi başlatın.\n"
            "2) Bir bilgisayardan diğerinin IP ve portuna bağlanın.\n"
            "3) İki tarafta da aynı anahtarı kullanın."
        )
        ctk.CTkLabel(
            parent,
            text=help_text,
            justify="left",
            wraplength=255,
            text_color="gray75",
        ).grid(row=6, column=0, padx=18, pady=(12, 0), sticky="w")

    def _build_listen_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Dinleme Portu").grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        self.listen_port_entry = ctk.CTkEntry(box)
        self.listen_port_entry.insert(0, str(DEFAULT_PORT))
        self.listen_port_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkButton(box, text="Dinlemeyi Başlat", command=self.start_listening).grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

    def _build_connect_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Karşı Bilgisayar IP").grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        self.peer_ip_entry = ctk.CTkEntry(box, placeholder_text="Örn: 192.168.1.25")
        self.peer_ip_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box, text="Karşı Port").grid(
            row=2, column=0, padx=12, pady=(4, 4), sticky="w"
        )
        self.peer_port_entry = ctk.CTkEntry(box)
        self.peer_port_entry.insert(0, str(DEFAULT_PORT))
        self.peer_port_entry.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkButton(box, text="Bağlan", command=self.connect_to_peer).grid(
            row=4, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

    def _build_key_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Yerel Şifreleme Anahtarı").grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        self.key_entry = ctk.CTkEntry(box)
        self.key_entry.insert(0, DEFAULT_KEY)
        self.key_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            box,
            text="6x6 Matrisi Göster",
            fg_color="gray30",
            hover_color="gray25",
            command=self.show_matrix,
        ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _build_status_box(self, parent: ctk.CTkFrame, row: int) -> None:
        box = ctk.CTkFrame(parent)
        box.grid(row=row, column=0, padx=14, pady=8, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            box, text="●", text_color="red", font=ctk.CTkFont(size=18)
        )
        self.status_dot.grid(row=0, column=0, padx=(12, 4), pady=12)

        self.status_label = ctk.CTkLabel(
            box, text="Bağlantı yok", wraplength=220, justify="left"
        )
        self.status_label.grid(row=0, column=1, padx=(4, 12), pady=12, sticky="w")

    def _build_chat_area(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.chat_title_label = ctk.CTkLabel(
            header, text="Şifreli Sohbet", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.chat_title_label.grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")

        self.peer_name_label = ctk.CTkLabel(
            header, text="Kiminle: Bağlantı yok", text_color="gray75"
        )
        self.peer_name_label.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

        ctk.CTkLabel(header, text=f"Oturum: {self.username}", text_color="gray75").grid(
            row=0, column=1, rowspan=2, padx=14, pady=12, sticky="e"
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

        port = self._read_port(self.peer_port_entry, "Karşı port")
        if port is not None:
            self.peer.connect(host, port)

    def send_message(self) -> None:
        raw_message = self.message_entry.get()
        if not raw_message.strip():
            return

        cipher = self._playfair()
        plaintext = cipher.normalize(raw_message)
        if not plaintext.strip():
            messagebox.showwarning(
                "Mesaj Gönderilemedi",
                "Mesaj, desteklenen karakterlerden en az birini içermeli.",
            )
            return

        ciphertext = cipher.encrypt(plaintext)
        payload = {
            "type": "message",
            "sender": self.username,
            "ciphertext": ciphertext,
            "timestamp": now_iso(),
        }

        if self.peer.send_payload(payload):
            self.db.save_message(self.username, self.peer.peer_address, "OUT", plaintext, ciphertext)
            self._add_message_bubble(f"Ben: {plaintext}\nŞifreli: {ciphertext}", outgoing=True)
            self.message_entry.delete(0, "end")

    def show_matrix(self) -> None:
        messagebox.showinfo("6x6 Türkçe Playfair Matrisi", self._playfair().matrix_as_text())

    # ---------- Ağ mesajları ----------

    def _on_network_connection(self, addr: tuple[str, int]) -> None:
        self.after(0, lambda: self._handle_connection_change(addr))

    def _handle_connection_change(self, addr: tuple[str, int]) -> None:
        if addr == ("", 0):
            self.peer_username = "Bağlantı yok"
            self._set_status("Bağlantı yok", connected=False)
            self._refresh_peer_header()
            return

        self.peer_username = f"{addr[0]}:{addr[1]}"
        self._set_status(f"Bağlı: {self.peer_username}", connected=True)
        self._refresh_peer_header()
        self._send_hello()

    def _send_hello(self) -> None:
        self.peer.send_payload({
            "type": "hello",
            "sender": self.username,
            "timestamp": now_iso(),
        })

    def _on_network_message(self, payload: dict[str, Any], addr: tuple[str, int]) -> None:
        self.after(0, lambda: self._handle_network_message(payload, addr))

    def _handle_network_message(self, payload: dict[str, Any], addr: tuple[str, int]) -> None:
        message_type = payload.get("type")

        if message_type == "hello":
            self._update_peer_name(str(payload.get("sender", "Karşı taraf")))
            return

        if message_type != "message":
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
        self.db.save_message(self.username, peer_address, "IN", plaintext, ciphertext)
        self._add_message_bubble(f"{sender}: {plaintext}\nŞifreli: {ciphertext}", outgoing=False)

    def _on_network_status(self, text: str) -> None:
        self.after(0, lambda: self._set_status(text, connected=self.peer.connected))

    def _on_network_error(self, text: str) -> None:
        self.after(0, lambda: self._set_status(text, connected=self.peer.connected, error=True))

    # ---------- Yardımcı metotlar ----------

    def _playfair(self) -> Playfair6x6:
        return Playfair6x6(self.key_entry.get().strip() or DEFAULT_KEY)

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

        self._add_system_message("Son mesaj geçmişi yüklendi.")
        for row in rows:
            who = "Ben" if row["direction"] == "OUT" else "Karşı taraf"
            text = f"{who} ({row['created_at']}): {row['plaintext']}\nŞifreli: {row['ciphertext']}"
            self._add_message_bubble(text, outgoing=row["direction"] == "OUT")

    def _add_system_message(self, text: str) -> None:
        label = ctk.CTkLabel(self.chat_area, text=text, text_color="gray70", justify="center")
        label.grid(row=self._message_row, column=0, padx=12, pady=6, sticky="ew")
        self._message_row += 1

    def _add_message_bubble(self, text: str, outgoing: bool) -> None:
        bubble = ctk.CTkLabel(
            self.chat_area,
            text=text,
            justify="left",
            anchor="w",
            wraplength=590,
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
        self._message_row += 1

    def close_app(self) -> None:
        self.peer.stop()
        self.db.close()
        self.destroy()
        self.master_window.destroy()
