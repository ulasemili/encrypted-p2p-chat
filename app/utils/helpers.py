from __future__ import annotations

import socket
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_local_ip() -> str:
    """LAN IP adresini bulur. Ağ yoksa 127.0.0.1 döner."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
