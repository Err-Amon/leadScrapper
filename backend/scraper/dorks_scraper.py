import logging
import requests
from urllib.parse import urlparse

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

from core.config import (
    BATCH_SIZE,
    MAX_CONSECUTIVE_FAILURES,
    ENRICHER_TIMEOUT,
)
from database.models import insert_lead, update_task_status
from parser.extractor import parse_page_contacts
from processing.cleaner import clean_lead
from utils.helpers import (
    RequestSession,
    CaptchaError,
    BlockedError,
    random_delay,
    page_turn_delay,
)
from utils.logger import get_logger

logger = get_logger(__name__)

CONTACT_PAGE_PATHS = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/reach-us",
    "/get-in-touch",
    "/team",
    "/our-team",
    "/staff",
    "/support",
    "/help",
]

BLOCKED_DOMAINS = frozenset(
    {
        "google.com",
        "google.co.uk",
        "youtube.com",
        "facebook.com",
        "twitter.com",
        "x.com",
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
        "medium.com",
        "quora.com",
        "apple.com",
        "microsoft.com",
        "yahoo.com",
        "bing.com",
    }
)


def run_dorks_scrape(
    task_id: str,
    task_logger: logging.Logger,
    task_manager=None,
    dork_query: str = "",
    max_results: int = 20,
    **kwargs,
) -> None:
    if not google_search and not DDGS:
        msg = "No search engine available. Install ddgs or googlesearch-python."
        task_logger.error(msg)
        update_task_status(task_id, status="failed", error=msg)
        return

    task_logger.info(
        f"Dorks scraper started | query='{dork_query}' | max={max_results}"
    )
    update_task_status(task_id, status="running", progress=0, total=max_results)

    session = RequestSession()
    collected = 0
    visited_domains: set[str] = set()

    try:
        url_generator = _search_urls(dork_query, max_results, task_logger)
        batch: list[dict] = []

        for url in url_generator:
            if task_manager and task_manager.is_task_cancelled(task_id):
                task_logger.info("Task cancelled — stopping dorks scrape.")
                return

            domain = _extract_domain(url)
            if not domain or domain in BLOCKED_DOMAINS or domain in visited_domains:
                task_logger.debug(f"Skipping: {url}")
                continue

            visited_domains.add(domain)
            task_logger.info(f"Visiting: {url}")

            raw = _scrape_url_for_contacts(url, domain, session, task_logger)
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
                task_logger.info(f"Batch processed | saved={saved} | total={collected}")
                batch.clear()
                random_delay()

            if collected >= max_results:
                break

        if batch and collected < max_results:
            saved = _process_batch(batch, task_id, dork_query, task_logger)
            collected += saved
            batch.clear()

    except CaptchaError:
        msg = (
            "Google returned a CAPTCHA page — the scraper has been blocked. "
            "Wait a few minutes and try again."
        )
        task_logger.error(msg)
        update_task_status(task_id, status="failed", error=msg)
        return

    except Exception as exc:
        task_logger.error(f"Dorks scraper unhandled error: {exc}")
        raise

    finally:
        session.close()

    task_logger.info(f"Dorks scrape complete | leads saved: {collected}")
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
    fetch_count = min(max_results * 3, 5000)

    if DDGS:
        task_logger.info(f"Running DuckDuckGo search: '{query}'")
        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        query,
                        max_results=fetch_count,
                        region="wt-wt",
                        safesearch="off",
                    )
                )
                task_logger.info(f"DuckDuckGo returned {len(results)} results")
                for r in results:
                    url = r.get("href", "")
                    if url and url.startswith("http"):
                        task_logger.debug(f"DDG result: {url}")
                        yield url
                        random_delay()
                if len(results) > 0:
                    return
        except Exception as exc:
            task_logger.warning(f"DuckDuckGo search error, trying Google: {exc}")

    if google_search:
        task_logger.info(f"Running Google dork search: '{query}'")
        try:
            found = 0
            for url in google_search(
                query,
                num_results=fetch_count,
                lang="en",
                sleep_interval=2,
            ):
                if url and url.startswith("http"):
                    task_logger.debug(f"Google result: {url}")
                    found += 1
                    yield url
                    random_delay()
            if found > 0:
                return
        except Exception as exc:
            task_logger.warning(f"Google search error: {exc}")

    task_logger.warning("No search engine returned results")


def _scrape_url_for_contacts(
    url: str,
    domain: str,
    session: RequestSession,
    task_logger: logging.Logger,
) -> dict | None:
    contacts = {
        "emails": [],
        "phones": [],
        "name": "",
        "address": "",
        "website": url,
        "social_links": [],
    }
    consecutive_failures = 0

    task_logger.info(f"Fetching homepage: {url}")
    html = _fetch_safe(url, session, task_logger)
    if html:
        _merge_contacts(contacts, parse_page_contacts(html, source_url=url))
        consecutive_failures = 0
        task_logger.info(
            f"After homepage: {len(contacts['emails'])} email(s), {len(contacts['phones'])} phone(s)"
        )
    else:
        consecutive_failures += 1
        task_logger.warning(f"Failed to fetch homepage: {url}")

    if not contacts["emails"] or not contacts["phones"]:
        for path in CONTACT_PAGE_PATHS:
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                task_logger.debug(
                    f"Too many failures for {domain} — skipping sub-pages."
                )
                break

            if contacts["emails"] and contacts["phones"]:
                break

            sub_url = f"https://{domain}{path}"
            if sub_url == url:
                continue

            task_logger.debug(f"Trying contact page: {sub_url}")
            sub_html = _fetch_safe(sub_url, session, task_logger)
            if sub_html:
                _merge_contacts(
                    contacts, parse_page_contacts(sub_html, source_url=sub_url)
                )
                consecutive_failures = 0
                task_logger.info(
                    f"After {path}: {len(contacts['emails'])} email(s), {len(contacts['phones'])} phone(s)"
                )
            else:
                consecutive_failures += 1
                task_logger.debug(f"Failed to fetch: {sub_url}")

            random_delay()

    if contacts["emails"]:
        task_logger.info(f"Found email: {contacts['emails'][0]}")
    else:
        task_logger.warning(f"No email found for {domain}")

    if contacts["phones"]:
        task_logger.info(f"Found phone: {contacts['phones'][0]}")
    else:
        task_logger.warning(f"No phone found for {domain}")

    if contacts.get("social_links"):
        task_logger.info(
            f"Found social links: {', '.join(contacts['social_links'][:3])}"
        )
    else:
        task_logger.info(f"No social links found for {domain}")

    if not any([contacts["emails"], contacts["phones"], contacts["name"]]):
        return None

    return {
        "name": contacts["name"],
        "email": contacts["emails"][0] if contacts["emails"] else "",
        "phone": contacts["phones"][0] if contacts["phones"] else "",
        "website": _root_url(url),
        "address": contacts["address"],
        "rating": None,
        "source": "dorks",
        "social_links": contacts.get("social_links", []),
    }


def _fetch_safe(
    url: str,
    session: RequestSession,
    task_logger: logging.Logger,
) -> str | None:
    try:
        return session.get(url, timeout=ENRICHER_TIMEOUT)

    except CaptchaError:
        raise

    except BlockedError as exc:
        task_logger.debug(f"Blocked fetching {url}: {exc}")
        page_turn_delay()
        return None

    except requests.exceptions.Timeout:
        task_logger.debug(f"Timeout: {url}")
        return None

    except requests.exceptions.TooManyRedirects:
        task_logger.debug(f"Too many redirects: {url}")
        return None

    except requests.exceptions.ConnectionError:
        task_logger.debug(f"Connection error: {url}")
        return None

    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code if exc.response else "?"
        task_logger.debug(f"HTTP {code}: {url}")
        return None

    except Exception as exc:
        task_logger.debug(f"Unexpected fetch error {url}: {exc}")
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
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _root_url(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return url


def _merge_contacts(target: dict, source: dict) -> None:
    for email in source.get("emails", []):
        if email not in target["emails"]:
            target["emails"].append(email)

    for phone in source.get("phones", []):
        if phone not in target["phones"]:
            target["phones"].append(phone)

    if not target["name"] and source.get("name"):
        target["name"] = source["name"]

    if not target["address"] and source.get("address"):
        target["address"] = source["address"]

    for link in source.get("social_links", []):
        if link not in target["social_links"]:
            target["social_links"].append(link)
