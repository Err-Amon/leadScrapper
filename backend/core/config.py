import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR.parent / "storage"
EXPORTS_DIR = STORAGE_DIR / "exports"
LOGS_DIR = BASE_DIR.parent / "logs"
DB_PATH = STORAGE_DIR / "database.db"

# Ensure directories exist at import time
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

BATCH_SIZE = 10  # Records processed per batch (memory guard)
MAX_WORKERS = 3  # Max concurrent background task workers
REQUEST_DELAY_MIN = 1.5  # Seconds — minimum delay between HTTP requests
REQUEST_DELAY_MAX = 3.5  # Seconds — maximum delay between HTTP requests
REQUEST_TIMEOUT = 10  # Seconds — per-request timeout
MAX_RETRIES = 3  # Retry attempts on transient failures
MAX_RESULTS_DEFAULT = 20  # Default result limit if user doesn't specify

ENRICHER_MAX_PAGES_PER_DOMAIN = 3  # Max pages visited per website during enrichment
ENRICHER_TIMEOUT = 5  # Tight timeout for enrichment requests
ENRICHER_MAX_CONCURRENT = 5  # Max websites enriched simultaneously

EXPORT_CHUNK_SIZE = 100  # Rows read from DB at a time during CSV generation

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
