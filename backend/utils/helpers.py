import time
import random
import functools
from urllib.parse import urlparse, urlunparse
from typing import Callable, Any

from core.config import (
    USER_AGENTS,
    DEFAULT_HEADERS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def random_delay() -> None:
    """Sleep for a random duration between configured min/max to avoid rate-limiting."""
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    time.sleep(delay)


def get_random_headers() -> dict:
    """Return request headers with a randomly chosen User-Agent."""
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers


def normalize_url(url: str) -> str:

    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    # Rebuild cleanly
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def retry(max_attempts: int = MAX_RETRIES, delay: float = 2.0, backoff: float = 2.0):

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            wait = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed ({exc}). "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
                    wait *= backoff

        return wrapper

    return decorator


def safe_get(d: dict, *keys, default=None) -> Any:
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d
