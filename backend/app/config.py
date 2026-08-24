import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("QOC_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = Path(os.environ.get("QOC_UPLOAD_DIR", DATA_DIR / "uploads"))
DB_PATH = Path(os.environ.get("QOC_DB_PATH", DATA_DIR / "qoc.db"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SESSION_TTL_DAYS = 7
DEFAULT_ADMIN_USER = os.environ.get("QOC_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("QOC_ADMIN_PASSWORD", "admin123")
