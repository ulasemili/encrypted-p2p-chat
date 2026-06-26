from __future__ import annotations

import subprocess
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

def get_tailscale_ip() -> str:
    """Tailscale IPv4 adresini bulur. Tailscale yoksa uyarı döner."""
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=3,
        )

        if result.returncode != 0:
            return "Tailscale kapalı/kurulu değil"

        lines = result.stdout.strip().splitlines()
        if not lines:
            return "Tailscale IP bulunamadı"

        return lines[0]

    except FileNotFoundError:
        return "Tailscale kurulu değil"
    except Exception:
        return "Tailscale IP alınamadı"