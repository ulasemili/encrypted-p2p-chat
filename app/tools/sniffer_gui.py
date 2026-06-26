import socket
import threading
import customtkinter as ctk
from tkinter import messagebox


class SnifferGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sniffer Proxy - Ağ Trafiği İzleyici")
        self.geometry("850x600")

        self.server_socket = None
        self.running = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        top.grid_columnconfigure((1, 3, 5, 7), weight=1)

        ctk.CTkLabel(top, text="Dinlenecek IP").grid(row=0, column=0, padx=8, pady=8)
        self.listen_host_entry = ctk.CTkEntry(top)
        self.listen_host_entry.insert(0, "0.0.0.0")
        self.listen_host_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Dinlenecek Port").grid(row=0, column=2, padx=8, pady=8)
        self.listen_port_entry = ctk.CTkEntry(top)
        self.listen_port_entry.insert(0, "6060")
        self.listen_port_entry.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Hedef IP").grid(row=0, column=4, padx=8, pady=8)
        self.target_host_entry = ctk.CTkEntry(top)
        self.target_host_entry.insert(0, "127.0.0.1")
        self.target_host_entry.grid(row=0, column=5, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Hedef Port").grid(row=0, column=6, padx=8, pady=8)
        self.target_port_entry = ctk.CTkEntry(top)
        self.target_port_entry.insert(0, "5050")
        self.target_port_entry.grid(row=0, column=7, padx=8, pady=8, sticky="ew")

        self.start_button = ctk.CTkButton(top, text="Sniffer Başlat", command=self.start_sniffer)
        self.start_button.grid(row=1, column=0, columnspan=4, padx=8, pady=8, sticky="ew")

        self.clear_button = ctk.CTkButton(top, text="Ekranı Temizle", command=self.clear_log)
        self.clear_button.grid(row=1, column=4, columnspan=4, padx=8, pady=8, sticky="ew")

        self.log_box = ctk.CTkTextbox(self)
        self.log_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self.log("Sniffer hazır.")
        self.log("Gönderici cihaz, gerçek alıcıya değil bu sniffer'ın IP ve portuna bağlanmalı.")

    def log(self, text: str):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def clear_log(self):
        self.log_box.delete("1.0", "end")

    def start_sniffer(self):
        if self.running:
            messagebox.showinfo("Bilgi", "Sniffer zaten çalışıyor.")
            return

        try:
            listen_host = self.listen_host_entry.get().strip()
            listen_port = int(self.listen_port_entry.get().strip())
            target_host = self.target_host_entry.get().strip()
            target_port = int(self.target_port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Port değerleri sayı olmalı.")
            return

        self.running = True
        self.start_button.configure(state="disabled", text="Sniffer Çalışıyor")

        thread = threading.Thread(
            target=self.run_proxy,
            args=(listen_host, listen_port, target_host, target_port),
            daemon=True
        )
        thread.start()

    def run_proxy(self, listen_host, listen_port, target_host, target_port):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((listen_host, listen_port))
            self.server_socket.listen(1)

            self.log(f"[SNIFFER] Dinleniyor: {listen_host}:{listen_port}")
            self.log(f"[SNIFFER] Hedef: {target_host}:{target_port}")
            self.log("[SNIFFER] Bağlantı bekleniyor...")

            client_socket, client_address = self.server_socket.accept()
            self.log(f"[BAĞLANTI] Gönderici bağlandı: {client_address}")

            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((target_host, target_port))
            self.log("[BAĞLANTI] Gerçek hedefe bağlandı.")

            threading.Thread(
                target=self.forward,
                args=(client_socket, target_socket, "Gönderici -> Alıcı"),
                daemon=True
            ).start()

            threading.Thread(
                target=self.forward,
                args=(target_socket, client_socket, "Alıcı -> Gönderici"),
                daemon=True
            ).start()

        except Exception as e:
            self.log(f"[HATA] {e}")
            self.running = False
            self.start_button.configure(state="normal", text="Sniffer Başlat")

    def forward(self, source, destination, direction):
        while True:
            try:
                data = source.recv(4096)

                if not data:
                    break

                decoded = data.decode("utf-8", errors="replace")

                self.log("\n" + "=" * 60)
                self.log(f"[{direction}] Yakalanan veri:")
                self.log(decoded)
                self.log("=" * 60 + "\n")

                destination.sendall(data)

            except Exception as e:
                self.log(f"[HATA] {direction}: {e}")
                break

        try:
            source.close()
            destination.close()
        except Exception:
            pass


if __name__ == "__main__":
    app = SnifferGUI()
    app.mainloop()