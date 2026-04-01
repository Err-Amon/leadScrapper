import logging
import re
import requests
from urllib.parse import urljoin, urlparse

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None  # Handled gracefully at runtime

from core.config import BATCH_SIZE, REQUEST_TIMEOUT, ENRICHER_TIMEOUT
from database.models import insert_lead, update_task_status
from parser.extractor import parse_page_contacts
from processing.cleaner import clean_lead
from utils.helpers import get_random_headers, random_delay, retry
from utils.logger import get_logger

logger = get_logger(__name__)

# Pages to check on each domain for contact information
CONTACT_PAGE_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us"]

# Domains to skip entirely — they never yield useful lead data
BLOCKED_DOMAINS = frozenset(
    {
        "google.com",
        "google.co.uk",
        "youtube.com",
        "facebook.com",
        "twitter.com",
        "instagram.com",
        "linkedin.com",
        "wikipedia.org",
        "amazon.com",
        "yelp.com",
        "tripadvisor.com",
        "reddit.com",
        "pinterest.com",
        "tumblr.com",
        "blogger.com",
        "wordpress.com",
    }
)


def run_dorks_scrape(
    task_id: str,
    task_logger: logging.Logger,
    dork_query: str = "",
    max_results: int = 20,
    **kwargs,
) -> None:

    if not google_search:
        msg = (
            "googlesearch-python is not installed. Run: pip install googlesearch-python"
        )
        task_logger.error(msg)
        update_task_status(task_id, status="failed", error=msg)
        return

    task_logger.info(
        f"Dorks scraper started | query='{dork_query}' | max={max_results}"
    )
    update_task_status(task_id, status="running", progress=0, total=max_results)

    collected = 0
    visited_domains: set[str] = set()

    try:
        url_generator = _search_urls(dork_query, max_results, task_logger)
        batch: list[dict] = []

        for url in url_generator:
            domain = _extract_domain(url)

            if not domain or domain in BLOCKED_DOMAINS or domain in visited_domains:
                task_logger.debug(f"Skipping URL: {url}")
                continue

            visited_domains.add(domain)
            task_logger.info(f"Visiting: {url}")

            raw = _scrape_url_for_contacts(url, domain, task_logger)

            if raw:
                batch.append(raw)

            if len(batch) >= BATCH_SIZE:
                saved = _process_batch(batch, task_id, dork_query, task_logger)
                collected += saved
                update_task_status(
                    task_id,
                    status="running",
                    progress=collected,
                    total=max_results,
                )
                task_logger.info(
                    f"Batch processed | saved={saved} | running_total={collected}"
                )
                batch.clear()
                random_delay()

            if collected >= max_results:
                break

        # Flush the final partial batch
        if batch and collected < max_results:
            saved = _process_batch(batch, task_id, dork_query, task_logger)
            collected += saved
            batch.clear()

    except Exception as exc:
        task_logger.error(f"Dorks scraper error: {exc}")
        raise

    task_logger.info(f"Dorks scrape complete | total leads saved: {collected}")
    update_task_status(
        task_id,
        status="completed",
        progress=collected,
        total=collected,
    )


def _search_urls(
    query: str,
    max_results: int,
    task_logger: logging.Logger,
):

    task_logger.info(f"Running Google search: '{query}'")

    # We request more than max_results to account for blocked domains being skipped
    fetch_count = min(max_results * 3, 100)

    try:
        for url in google_search(
            query, num_results=fetch_count, lang="en", sleep_interval=2
        ):
            if url and url.startswith("http"):
                task_logger.debug(f"Search result URL: {url}")
                yield url
                random_delay()
    except Exception as exc:
        task_logger.warning(f"Google search error (may be rate-limited): {exc}")


def _scrape_url_for_contacts(
    url: str,
    domain: str,
    task_logger: logging.Logger,
) -> dict | None:

    contacts = {"emails": [], "phones": [], "name": "", "address": "", "website": url}

    # Step 1: Root page
    html = _fetch_page_safe(url, task_logger)
    if html:
        page_data = parse_page_contacts(html, source_url=url)
        _merge_contacts(contacts, page_data)

    # Step 2: Check contact/about sub-pages only if we still have no email
    if not contacts["emails"]:
        for path in CONTACT_PAGE_PATHS:
            sub_url = f"https://{domain}{path}"
            if sub_url == url:
                continue

            task_logger.debug(f"Checking contact page: {sub_url}")
            sub_html = _fetch_page_safe(sub_url, task_logger)

            if sub_html:
                sub_data = parse_page_contacts(sub_html, source_url=sub_url)
                _merge_contacts(contacts, sub_data)

            if contacts["emails"]:
                break  # Found an email — stop checking more sub-pages

            random_delay()

    # Build a single lead dict from all contacts found on this domain
    if not any([contacts["emails"], contacts["phones"], contacts["name"]]):
        return None

    return {
        "name": contacts["name"],
        "email": contacts["emails"][0] if contacts["emails"] else "",
        "phone": contacts["phones"][0] if contacts["phones"] else "",
        "website": _clean_website_url(url),
        "address": contacts["address"],
        "rating": None,
        "source": "dorks",
    }


@retry(max_attempts=2, delay=1.5, backoff=2.0)
def _fetch_page_safe(url: str, task_logger: logging.Logger) -> str | None:

    try:
        headers = get_random_headers()
        response = requests.get(
            url,
            headers=headers,
            timeout=ENRICHER_TIMEOUT,
            allow_redirects=True,
        )

        # Only process HTML responses — skip PDFs, images, etc.
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            task_logger.debug(f"Skipping non-HTML response: {url} ({content_type})")
            return None

        response.raise_for_status()
        return response.text

    except requests.exceptions.Timeout:
        task_logger.debug(f"Timeout fetching: {url}")
        return None
    except requests.exceptions.TooManyRedirects:
        task_logger.debug(f"Too many redirects: {url}")
        return None
    except requests.exceptions.ConnectionError:
        task_logger.debug(f"Connection error: {url}")
        return None
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response else "?"
        task_logger.debug(f"HTTP {status} for: {url}")
        return None
    except Exception as exc:
        task_logger.debug(f"Unexpected error fetching {url}: {exc}")
        return None


def _process_batch(
    batch: list[dict],
    task_id: str,
    dork_query: str,
    task_logger: logging.Logger,
) -> int:

    saved = 0

    for raw in batch:
        raw["source"] = "dorks"
        raw["keyword"] = dork_query

        cleaned = clean_lead(raw)

        # Skip records with absolutely no useful contact data
        if not any(
            [cleaned["name"], cleaned["phone"], cleaned["email"], cleaned["website"]]
        ):
            task_logger.debug("Skipping empty dork record.")
            continue

        row_id = insert_lead(task_id=task_id, **cleaned)

        if row_id:
            saved += 1
            task_logger.debug(
                f"Saved #{row_id}: '{cleaned['name']}' | "
                f"email={cleaned['email'] or '-'} | phone={cleaned['phone'] or '-'}"
            )
        else:
            task_logger.debug(
                f"Duplicate skipped: '{cleaned['name']}' / {cleaned['email']}"
            )

    return saved


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _clean_website_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url


def _merge_contacts(target: dict, source: dict) -> None:

    # Merge email list — deduplicate preserving order
    existing_emails = set(target["emails"])
    for email in source.get("emails", []):
        if email not in existing_emails:
            target["emails"].append(email)
            existing_emails.add(email)

    # Merge phone list — deduplicate preserving order
    existing_phones = set(target["phones"])
    for phone in source.get("phones", []):
        if phone not in existing_phones:
            target["phones"].append(phone)
            existing_phones.add(phone)

    # Take name and address only if we don't already have them
    if not target["name"] and source.get("name"):
        target["name"] = source["name"]

    if not target["address"] and source.get("address"):
        target["address"] = source["address"]
