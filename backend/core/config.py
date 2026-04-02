import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR.parent / "storage"
EXPORTS_DIR = STORAGE_DIR / "exports"
LOGS_DIR = BASE_DIR.parent / "logs"
DB_PATH = STORAGE_DIR / "database.db"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

BATCH_SIZE = 10  # Records per processing batch (memory guard)
MAX_WORKERS = 3  # Concurrent background task workers
REQUEST_TIMEOUT = 12  # Seconds per HTTP request
MAX_RETRIES = 3  # Retry attempts on transient failures
MAX_RESULTS_DEFAULT = 20  # Default result cap

REQUEST_DELAY_MIN = 2.0  # Minimum seconds between requests
REQUEST_DELAY_MAX = 5.0  # Maximum seconds between requests
JITTER_MIN = 0.3  # Extra random jitter added to each delay (min)
JITTER_MAX = 1.2  # Extra random jitter added to each delay (max)
PAGE_TURN_DELAY_MIN = 3.0  # Extra pause between paginated page fetches
PAGE_TURN_DELAY_MAX = 7.0  # Simulates reading time between pages

MAX_CONSECUTIVE_FAILURES = 4  # Abort scrape after this many back-to-back errors
BACKOFF_BASE_DELAY = 2.0  # Base seconds for exponential backoff
BACKOFF_MULTIPLIER = 2.0  # Multiplier per retry attempt
BACKOFF_MAX_DELAY = 30.0  # Cap backoff at this many seconds

SESSION_MAX_REQUESTS = 15
CAPTCHA_INDICATORS = [
    "unusual traffic",
    "captcha",
    "recaptcha",
    "please verify you",
    "are you a robot",
    "detected unusual activity",
    "automated queries",
    "sorry, we can't verify",
    "enable javascript and cookies",
    "/sorry/index",
    "google.com/sorry",
]

BLOCK_STATUS_CODES = {429, 503, 403}

ENRICHER_MAX_PAGES_PER_DOMAIN = 3
ENRICHER_TIMEOUT = 6  # Slightly more generous than Phase 5
ENRICHER_MAX_CONCURRENT = 5

EXPORT_CHUNK_SIZE = 100

# Google Maps API configuration (recommended - more reliable than scraping)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# ScraperAPI configuration (handles Google's anti-scraping measures)
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_URL = "http://api.scraperapi.com"

TASK_SHUTDOWN_TIMEOUT = 30  # Seconds to wait for running tasks on server shutdown

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "DNT": "1",
}
