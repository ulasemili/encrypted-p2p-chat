from __future__ import annotations

import json
import socket
import threading
from typing import Any, Callable

from app.config import ENCODING

MessageCallback = Callable[[dict[str, Any], tuple[str, int]], None]
TextCallback = Callable[[str], None]
ConnectionCallback = Callable[[tuple[str, int]], None]


class PeerNode:
    """TCP ile çalışan basit P2P düğüm."""

    def __init__(
        self,
        on_message: MessageCallback,
        on_status: TextCallback,
        on_error: TextCallback,
        on_connection: ConnectionCallback,
    ) -> None:
        self.on_message = on_message
        self.on_status = on_status
        self.on_error = on_error
        self.on_connection = on_connection

        self._server: socket.socket | None = None
        self._conn: socket.socket | None = None
        self._addr: tuple[str, int] | None = None
        self._stop = threading.Event()
        self._send_lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._conn is not None

    @property
    def peer_address(self) -> str:
        if self._addr is None:
            return "Bağlantı yok"
        return f"{self._addr[0]}:{self._addr[1]}"

    def start_server(self, port: int, host: str = "0.0.0.0") -> None:
        if self._server is not None:
            self.on_status("Dinleme zaten aktif.")
            return

        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((host, port))
            self._server.listen(5)
            self._server.settimeout(1.0)
        except OSError as exc:
            self.on_error(f"Port dinlenemedi: {exc}")
            self.stop()
            return

        self._stop.clear()
        threading.Thread(target=self._accept_loop, daemon=True).start()
        self.on_status(f"Dinleniyor: {host}:{port}")

    def connect(self, host: str, port: int) -> None:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(8.0)
            conn.connect((host, port))
            conn.settimeout(1.0)
        except OSError as exc:
            self.on_error(f"Bağlantı kurulamadı: {exc}")
            return

        self._use_connection(conn, (host, port))
        self.on_status(f"Bağlanıldı: {host}:{port}")

    def send_payload(self, payload: dict[str, Any]) -> bool:
        if self._conn is None:
            self.on_error("Aktif bağlantı yok. Önce karşı bilgisayara bağlanın.")
            return False

        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode(ENCODING)
        try:
            with self._send_lock:
                self._conn.sendall(data)
            return True
        except OSError as exc:
            self.on_error(f"Mesaj gönderilemedi: {exc}")
            return False

    def stop(self) -> None:
        self._stop.set()
        self._close_socket(self._server)
        self._close_socket(self._conn)
        self._server = None
        self._conn = None
        self._addr = None

    def _accept_loop(self) -> None:
        while not self._stop.is_set() and self._server is not None:
            try:
                conn, addr = self._server.accept()
                conn.settimeout(1.0)
                self._use_connection(conn, addr)
                self.on_status(f"Gelen bağlantı kabul edildi: {addr[0]}:{addr[1]}")
            except socket.timeout:
                continue
            except OSError:
                break

    def _use_connection(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        self._close_socket(self._conn)
        self._conn = conn
        self._addr = addr
        self.on_connection(addr)
        threading.Thread(target=self._receive_loop, args=(conn, addr), daemon=True).start()

    def _receive_loop(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        buffer = ""
        while not self._stop.is_set():
            try:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data.decode(ENCODING)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self._handle_line(line, addr)

            except socket.timeout:
                continue
            except OSError:
                break

        if self._conn is conn:
            self._conn = None
            self._addr = None
            self.on_connection(("", 0))

    def _handle_line(self, line: str, addr: tuple[str, int]) -> None:
        try:
            self.on_message(json.loads(line), addr)
        except json.JSONDecodeError:
            self.on_error("Geçersiz ağ paketi alındı.")

    @staticmethod
    def _close_socket(sock: socket.socket | None) -> None:
        if sock is None:
            return
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
