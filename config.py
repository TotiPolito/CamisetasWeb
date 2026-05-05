from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
PERSISTENT_ROOT = Path(os.getenv("PERSISTENT_ROOT", BASE_DIR / "storage")).resolve()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambiar-esta-clave-antes-de-publicar")
    DATABASE_PATH = PERSISTENT_ROOT / "catalog.sqlite3"
    MEDIA_ROOT = PERSISTENT_ROOT / "media"
    MEDIA_CACHE_ROOT = PERSISTENT_ROOT / "cache" / "media"
    PRODUCT_SEED_PATH = BASE_DIR / "data" / "products.json"
    DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")
    MAX_CONTENT_LENGTH = 512 * 1024 * 1024
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_BLOCK_SECONDS = int(os.getenv("LOGIN_BLOCK_SECONDS", "300"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
