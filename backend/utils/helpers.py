import time
import random
import functools
import threading
import requests
from urllib.parse import urlparse, urlunparse
from typing import Callable, Any

from core.config import (
    USER_AGENTS,
    DEFAULT_HEADERS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    JITTER_MIN,
    JITTER_MAX,
    PAGE_TURN_DELAY_MIN,
    PAGE_TURN_DELAY_MAX,
    BACKOFF_BASE_DELAY,
    BACKOFF_MULTIPLIER,
    BACKOFF_MAX_DELAY,
    MAX_RETRIES,
    SESSION_MAX_REQUESTS,
    CAPTCHA_INDICATORS,
    BLOCK_STATUS_CODES,
    REQUEST_TIMEOUT,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class CaptchaError(Exception):
    """Raised when a response page appears to be a CAPTCHA or block page."""


class BlockedError(Exception):
    """Raised when a response HTTP status indicates rate-limiting or blocking."""


def is_captcha_response(html: str) -> bool:
    if not html:
        return False
    lower = html.lower()
    return any(indicator in lower for indicator in CAPTCHA_INDICATORS)


def is_blocked_status(status_code: int) -> bool:
    return status_code in BLOCK_STATUS_CODES


def random_delay() -> None:
    base = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    jitter = random.uniform(JITTER_MIN, JITTER_MAX)
    time.sleep(base + jitter)


def human_delay() -> None:
    random_delay()


def page_turn_delay() -> None:
    delay = random.uniform(PAGE_TURN_DELAY_MIN, PAGE_TURN_DELAY_MAX)
    logger.debug(f"Page-turn delay: {delay:.1f}s")
    time.sleep(delay)


def backoff_delay(attempt: int) -> None:
    raw = BACKOFF_BASE_DELAY * (BACKOFF_MULTIPLIER ** (attempt - 1))
    capped = min(raw, BACKOFF_MAX_DELAY)
    jitter = random.uniform(0, capped * 0.25)  # Up to 25% extra jitter
    delay = capped + jitter
    logger.debug(f"Backoff delay attempt={attempt}: {delay:.1f}s")
    time.sleep(delay)


def get_random_headers() -> dict:
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers


class RequestSession:
    def __init__(self):
        self._lock = threading.Lock()
        self._session = self._new_session()
        self._request_count = 0

    def _new_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        s.headers["User-Agent"] = random.choice(USER_AGENTS)
        return s

    def _maybe_recycle(self) -> None:
        if self._request_count >= SESSION_MAX_REQUESTS:
            logger.debug(f"Recycling HTTP session after {self._request_count} requests")
            try:
                self._session.close()
            except Exception:
                pass
            self._session = self._new_session()
            self._request_count = 0

    def get(
        self,
        url: str,
        timeout: int = REQUEST_TIMEOUT,
        allow_redirects: bool = True,
        check_captcha: bool = True,
    ) -> str | None:
        with self._lock:
            self._maybe_recycle()
            # Rotate User-Agent on every request
            self._session.headers["User-Agent"] = random.choice(USER_AGENTS)

        response = self._session.get(
            url,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )

        with self._lock:
            self._request_count += 1

        if is_blocked_status(response.status_code):
            raise BlockedError(
                f"HTTP {response.status_code} — likely rate-limited: {url}"
            )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        html = response.text

        if check_captcha and is_captcha_response(html):
            raise CaptchaError(f"CAPTCHA detected at: {url}")

        return html

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass


def retry(
    max_attempts: int = MAX_RETRIES,
    delay: float = BACKOFF_BASE_DELAY,
    backoff: float = BACKOFF_MULTIPLIER,
    reraise_captcha: bool = True,
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            wait = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)

                except CaptchaError as exc:
                    # Never retry on CAPTCHA — it won't help
                    if reraise_captcha:
                        logger.warning(f"{func.__name__} blocked by CAPTCHA: {exc}")
                        raise
                    attempt += 1

                except BlockedError as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} still blocked after "
                            f"{max_attempts} attempts: {exc}"
                        )
                        raise
                    # Use a longer backoff for block errors
                    longer_wait = min(wait * 3, BACKOFF_MAX_DELAY)
                    logger.warning(
                        f"{func.__name__} blocked (attempt {attempt}): {exc}. "
                        f"Waiting {longer_wait:.1f}s…"
                    )
                    time.sleep(longer_wait)
                    wait = min(wait * backoff, BACKOFF_MAX_DELAY)

                except Exception as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    capped_wait = min(wait, BACKOFF_MAX_DELAY)
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed ({exc}). "
                        f"Retrying in {capped_wait:.1f}s…"
                    )
                    time.sleep(capped_wait)
                    wait = min(wait * backoff, BACKOFF_MAX_DELAY)

        return wrapper

    return decorator


def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def safe_get(d: dict, *keys, default=None) -> Any:
    current: Any = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current
