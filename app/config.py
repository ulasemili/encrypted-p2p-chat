from pathlib import Path

APP_NAME = "Şifreli P2P Haberleşme"
DEFAULT_PORT = 5050
DEFAULT_KEY = "türkiyem!"
ENCODING = "utf-8"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "chat.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
