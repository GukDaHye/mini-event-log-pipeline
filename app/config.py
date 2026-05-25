import os
from pathlib import Path


EVENT_WEIGHTS = {
    "page_view": 0.45,
    "product_view": 0.25,
    "add_to_cart": 0.12,
    "purchase": 0.08,
    "error": 0.10,
}

EVENT_COUNT = int(os.getenv("EVENT_COUNT", "1000"))
USER_COUNT = int(os.getenv("USER_COUNT", "50"))
MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
RECENT_HOURS = int(os.getenv("RECENT_HOURS", "24"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "commerce_events"),
    "user": os.getenv("DB_USER", "commerce_user"),
    "password": os.getenv("DB_PASSWORD", "commerce_password"),
}
