from __future__ import annotations

import hashlib
import sqlite3
import threading
from pathlib import Path
from typing import Iterable

from app.config import DB_PATH


class Database:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self) -> None:
        with self._lock, self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    peer_address TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('IN', 'OUT')),
                    plaintext TEXT NOT NULL,
                    ciphertext TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def password_hash(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def add_user(self, username: str, password: str) -> bool:
        username = username.strip()
        if not username or not password:
            return False
        try:
            with self._lock, self.conn:
                self.conn.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    (username, self.password_hash(password)),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username: str, password: str) -> bool:
        with self._lock:
            row = self.conn.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if row is None:
            return False
        return row["password_hash"] == self.password_hash(password)

    def user_count(self) -> int:
        with self._lock:
            row = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return int(row["c"])

    def save_message(
        self,
        username: str,
        peer_address: str,
        direction: str,
        plaintext: str,
        ciphertext: str,
    ) -> None:
        with self._lock, self.conn:
            self.conn.execute(
                """
                INSERT INTO messages(username, peer_address, direction, plaintext, ciphertext)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, peer_address, direction, plaintext, ciphertext),
            )

    def get_recent_messages(self, username: str, limit: int = 50) -> list[sqlite3.Row]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT peer_address, direction, plaintext, ciphertext, created_at
                FROM messages
                WHERE username = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
        return list(reversed(rows))

    def close(self) -> None:
        with self._lock:
            self.conn.close()
