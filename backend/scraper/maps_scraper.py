import logging
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

from core.config import (
    BATCH_SIZE,
    REQUEST_TIMEOUT,
    MAX_CONSECUTIVE_FAILURES,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_MAPS_API_URL,
    SCRAPER_API_KEY,
    SCRAPER_API_URL,
    ENRICHER_TIMEOUT,
)
from database.models import insert_lead, update_task_status
from parser.extractor import (
    extract_phones,
    extract_emails,
    normalize_rating,
    parse_maps_listing,
    parse_page_contacts,
)
from processing.cleaner import clean_lead
from utils.helpers import (
    RequestSession,
    CaptchaError,
    BlockedError,
    get_random_headers,
    random_delay,
    page_turn_delay,
    retry,
    is_captcha_response,
)
from utils.logger import get_logger

logger = get_logger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"


def run_maps_scrape(
    task_id: str,
    task_logger: logging.Logger,
    task_manager=None,
    keyword: str = "",
    location: str = "",
    max_results: int = 20,
    **kwargs,
) -> None:
    task_logger.info(
        f"Maps scraper started | keyword='{keyword}' | "
        f"location='{location}' | max={max_results}"
    )
    update_task_status(task_id, status="running", progress=0, total=max_results)

    query = f"{keyword} {location}".strip()
    session = RequestSession()
    collected = 0

    try:
        # Use Google Maps API if configured (recommended - most reliable)
        if GOOGLE_MAPS_API_KEY:
            task_logger.info("Using Google Maps API for scraping")
            raw_listings = _fetch_via_maps_api(query, max_results, task_logger)
        # Use ScraperAPI if configured (handles anti-scraping)
        elif SCRAPER_API_KEY:
            task_logger.info("Using ScraperAPI for Google scraping")
            raw_listings = _fetch_via_scraper_api(
                query, max_results, session, task_logger
            )
        # Use DuckDuckGo as the primary free method (more reliable than direct Google)
        elif DDGS:
            task_logger.info("Using DuckDuckGo search for business listings")
            raw_listings = _fetch_via_duckduckgo(query, max_results, task_logger)
            # If DuckDuckGo returned nothing, try direct Google as last resort
            if not raw_listings:
                task_logger.info("DuckDuckGo returned 0 results, trying direct Google")
                raw_listings = _fetch_all_listings(
                    query, max_results, session, task_logger
                )
        # Last resort: direct Google scraping
        else:
            task_logger.info("Using direct Google scraping (may be less reliable)")
            raw_listings = _fetch_all_listings(query, max_results, session, task_logger)

        task_logger.info(f"Fetched {len(raw_listings)} raw listing blocks total")

        batch: list[dict] = []

        for raw in raw_listings:
            # Cancellation check — exit cleanly between batches
            if task_manager and task_manager.is_task_cancelled(task_id):
                task_logger.info("Task cancelled — stopping scrape.")
                return

            batch.append(raw)

            if len(batch) >= BATCH_SIZE:
                saved = _process_batch(batch, task_id, keyword, task_logger)
                collected += saved
                update_task_status(
                    task_id,
                    status="running",
                    progress=collected,
                    total=max_results,
                )
                task_logger.info(f"Batch done | saved={saved} | total={collected}")
                batch.clear()
                random_delay()

            if collected >= max_results:
                break

        # Flush final partial batch
        if batch and collected < max_results:
            saved = _process_batch(batch, task_id, keyword, task_logger)
            collected += saved
            batch.clear()

    except CaptchaError as exc:
        msg = (
            "Google returned a CAPTCHA page — the scraper has been blocked. "
            "Wait a few minutes and try again, or reduce max_results."
        )
        task_logger.error(msg)
        update_task_status(task_id, status="failed", error=msg)
        return

    except Exception as exc:
        task_logger.error(f"Maps scraper unhandled error: {exc}")
        raise

    finally:
        session.close()

    task_logger.info(f"Maps scrape complete | leads saved: {collected}")
    update_task_status(
        task_id,
        status="completed",
        progress=collected,
        total=collected,
    )


def _fetch_via_maps_api(
    query: str,
    max_results: int,
    task_logger: logging.Logger,
) -> list[dict]:
    """Fetch listings using Google Maps Places API (recommended method)."""
    all_listings = []

    params = {
        "query": query,
        "key": GOOGLE_MAPS_API_KEY,
        "max_results": min(max_results, 60),  # API max is 60 per request
    }

    try:
        response = requests.get(
            GOOGLE_MAPS_API_URL, params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            task_logger.error(
                f"Maps API error: {data.get('status')} - {data.get('error_message', '')}"
            )
            return all_listings

        for place in data.get("results", [])[:max_results]:
            listing = {
                "name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "phone": place.get("formatted_phone_number", ""),
                "website": place.get("website", ""),
                "rating": place.get("rating"),
                "email": "",  # Not available via API
            }
            if listing.get("name"):
                all_listings.append(listing)

        task_logger.info(f"Maps API returned {len(all_listings)} listings")

    except requests.exceptions.Timeout:
        task_logger.error("Maps API request timed out")
    except requests.exceptions.RequestException as exc:
        task_logger.error(f"Maps API request failed: {exc}")
    except Exception as exc:
        task_logger.error(f"Maps API parsing error: {exc}")

    return all_listings


def _fetch_via_duckduckgo(
    query: str,
    max_results: int,
    task_logger: logging.Logger,
) -> list[dict]:
    """Fetch business listings using DuckDuckGo search as fallback."""
    all_listings = []

    if not DDGS:
        task_logger.warning(
            "DuckDuckGo search not available (ddgs package not installed)"
        )
        return all_listings

    try:
        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query,
                    max_results=min(max_results * 3, 5000),
                    region="wt-wt",
                    safesearch="off",
                )
            )
            task_logger.info(f"DuckDuckGo returned {len(results)} results")

            for r in results:
                if len(all_listings) >= max_results:
                    break

                url = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")

                if not url or not url.startswith("http"):
                    continue

                skip_domains = {
                    "google.com",
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
                    "medium.com",
                    "quora.com",
                }
                try:
                    domain = urlparse(url).netloc.lower().replace("www.", "")
                    if any(d in domain for d in skip_domains):
                        continue
                except Exception:
                    continue

                phones = extract_phones(body)
                emails = extract_emails(body)

                listing = {
                    "name": title,
                    "address": "",
                    "phone": phones[0] if phones else "",
                    "website": url,
                    "rating": None,
                    "email": emails[0] if emails else "",
                }
                if listing["name"]:
                    all_listings.append(listing)

            task_logger.info(f"DuckDuckGo extracted {len(all_listings)} listings")

    except Exception as exc:
        task_logger.error(f"DuckDuckGo search error: {exc}")

    return all_listings


def _fetch_via_scraper_api(
    query: str,
    max_results: int,
    session: RequestSession,
    task_logger: logging.Logger,
) -> list[dict]:
    """Fetch listings using ScraperAPI (handles Google's anti-scraping)."""
    all_listings = []
    start = 0
    per_page = 10
    consecutive_failures = 0

    while len(all_listings) < max_results:
        scraper_url = (
            f"{SCRAPER_API_URL}/render?api_key={SCRAPER_API_KEY}"
            f"&url={GOOGLE_SEARCH_URL}?q={urlencode({'q': query, 'num': per_page, 'start': start})}"
            f"&render_js=true"
        )

        task_logger.info(f"Fetching via ScraperAPI: start={start}")

        try:
            response = requests.get(scraper_url, timeout=REQUEST_TIMEOUT * 2)
            response.raise_for_status()
            html = response.text

            if is_captcha_response(html):
                task_logger.warning("ScraperAPI returned a CAPTCHA page")
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    break
                continue

            consecutive_failures = 0
            page_listings = _parse_page(html)

            if not page_listings:
                task_logger.info("No listings found — ending pagination")
                break

            all_listings.extend(page_listings)
            task_logger.info(
                f"Page start={start} → {len(page_listings)} listings | "
                f"running total: {len(all_listings)}"
            )

            if len(page_listings) < per_page:
                break

            start += per_page
            random_delay()

        except requests.exceptions.Timeout:
            consecutive_failures += 1
            task_logger.warning(
                f"ScraperAPI timeout ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})"
            )
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                break
            random_delay()
        except Exception as exc:
            consecutive_failures += 1
            task_logger.warning(f"ScraperAPI error: {exc}")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                break
            random_delay()

    return all_listings[:max_results]


def _fetch_all_listings(
    query: str,
    max_results: int,
    session: RequestSession,
    task_logger: logging.Logger,
) -> list[dict]:
    all_listings: list[dict] = []
    start = 0
    per_page = 10
    consecutive_failures = 0

    while len(all_listings) < max_results:
        params = {
            "q": query,
            "num": per_page,
            "start": start,
            "hl": "en",
            "gl": "us",
        }
        url = f"{GOOGLE_SEARCH_URL}?{urlencode(params)}"
        task_logger.info(f"Fetching page start={start}")

        try:
            html = session.get(url, timeout=REQUEST_TIMEOUT)

        except CaptchaError:
            task_logger.warning("CAPTCHA hit — aborting pagination.")
            raise  # Propagate to run_maps_scrape for clean task failure

        except BlockedError as exc:
            consecutive_failures += 1
            task_logger.warning(f"Blocked (attempt {consecutive_failures}): {exc}")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                task_logger.error("Too many consecutive blocks — aborting.")
                break
            page_turn_delay()
            continue

        except requests.exceptions.Timeout:
            consecutive_failures += 1
            task_logger.warning(
                f"Timeout on page start={start} "
                f"({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})"
            )
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                task_logger.error("Too many consecutive timeouts — aborting.")
                break
            random_delay()
            continue

        except Exception as exc:
            consecutive_failures += 1
            task_logger.warning(
                f"Page fetch error start={start}: {exc} "
                f"({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})"
            )
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                task_logger.error("Too many consecutive failures — aborting.")
                break
            random_delay()
            continue

        if html is None:
            task_logger.debug(f"Non-HTML response at start={start} — skipping page.")
            start += per_page
            page_turn_delay()
            continue

        # Reset failure counter on a successful fetch
        consecutive_failures = 0

        page_listings = _parse_page(html)
        if not page_listings:
            task_logger.info("No listings found on page — ending pagination.")
            break

        all_listings.extend(page_listings)
        task_logger.info(
            f"Page start={start} → {len(page_listings)} listings | "
            f"running total: {len(all_listings)}"
        )

        if len(page_listings) < per_page:
            break  # Short page = no more results

        start += per_page
        page_turn_delay()  # Human-like pause between pages

    return all_listings[:max_results]


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    # Try JSON-LD structured data first (most reliable)
    listings = _parse_json_ld(soup)
    if listings:
        return listings

    # Try local cards (Google Maps integrations)
    listings = _parse_local_cards(soup)
    if listings:
        return listings

    # Fall back to organic search results
    return _parse_organic_blocks(soup)


def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    listings = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)

            # Handle both single items and arrays
            items = data if isinstance(data, list) else [data]

            for item in items:
                if (
                    item.get("@type") == "LocalBusiness"
                    or item.get("@type") == "Organization"
                ):
                    listing = {
                        "name": item.get("name", ""),
                        "address": item.get("address", {}).get("streetAddress", "")
                        if isinstance(item.get("address"), dict)
                        else "",
                        "phone": item.get("telephone", ""),
                        "website": item.get("url", ""),
                        "rating": item.get("aggregateRating", {}).get("ratingValue")
                        if isinstance(item.get("aggregateRating"), dict)
                        else None,
                        "email": item.get("email", ""),
                    }
                    if listing.get("name"):
                        listings.append(listing)
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    return listings


def _parse_local_cards(soup: BeautifulSoup) -> list[dict]:
    """Parse Google Maps local business cards."""
    # Updated selectors for current Google layout (2024-2025)
    card_selectors = [
        "div.Nv2PK",  # Current local pack container
        "div.cdl",  # Current Google Local results container
        "div.VkpGBb",
        "div.rllt__details",
        "div[data-cid]",  # Data attribute for business cards
        "div.uMdZh",
        "div.cXedhc",
        "div.mnr-c",
        "div.h5obzc",  # Recent layout
        "div[jscontroller]",  # Generic Google Maps container
        "div[data-async-context]",  # Async loaded content
    ]

    cards: list = []
    for selector in card_selectors:
        found = soup.select(selector)
        if found:
            cards = found
            break

    listings = []
    for card in cards:
        listing = _extract_card_fields(card)
        if listing.get("name"):
            listings.append(listing)
    return listings


def _parse_organic_blocks(soup: BeautifulSoup) -> list[dict]:
    """Parse organic search results for business information."""
    listings = []

    # Modern selectors for Google search results (2024-2025)
    block_selectors = [
        "div.g",  # Classic Google results container
        "div.tF2Cxc",  # Previous layout
        "div.wVrVMb",  # Current layout
        "div.kvH3mc",
        "div[data-sokoban-container]",  # Google's internal container marker
        "article",  # Semantic HTML5
        "div.MjjYud",  # Recent container class
        "div.hJR8md",  # Alternative container
    ]

    blocks = []
    for selector in block_selectors:
        found = soup.select(selector)
        if found:
            blocks = found
            break

    for block in blocks:
        listing = _extract_organic_fields(block)
        if any([listing.get("name"), listing.get("phone"), listing.get("email")]):
            listings.append(listing)
    return listings


def _extract_card_fields(card) -> dict:
    data = {"name": "", "address": "", "phone": "", "website": "", "rating": None}

    # Updated name selectors for current Google layout
    for selector in [
        "span.OSrXXb",  # Classic name selector
        "div.dbg0pd span",  # Business name in local pack
        "[role='heading']",  # ARIA heading for business name
        "h3",  # Standard heading
        "span[aria-label]",  # ARIA label (accessibility)
        "span.qBF1Pd",  # Recent name class
        "div.q8U8x span",  # Alternative name container
    ]:
        el = card.select_one(selector)
        if el:
            data["name"] = el.get_text(strip=True)
            break

    # Updated address selectors
    for selector in [
        "span.rllt__wrapped",  # Classic address wrapper
        "div.rllt__details > div:nth-child(2)",  # Details container
        "span.LrzXr",  # Address text
        "div.W4EYD",  # Recent address class
        "span.UsdlK",  # Alternative address
        "div[data-x-addr]",  # Data attribute for address
    ]:
        el = card.select_one(selector)
        if el:
            data["address"] = el.get_text(strip=True)
            break

    # Updated rating selectors
    rating_el = card.select_one(
        "span[aria-label*='Rated'], span[aria-label*='stars'], span.Aq14fc, "
        "span.YdS9Jc, div.uaOxqc span, span[aria-label*='rating']"
    )
    if rating_el:
        aria = rating_el.get("aria-label", "")
        match = re.search(r"(\d+\.?\d*)", aria)
        data["rating"] = normalize_rating(
            match.group(1) if match else rating_el.get_text(strip=True)
        )

    tel_link = card.select_one("a[href^='tel:']")
    if tel_link:
        data["phone"] = tel_link["href"].replace("tel:", "").strip()
    else:
        phones = extract_phones(card.get_text(" ", strip=True))
        if phones:
            data["phone"] = phones[0]

    site_link = card.select_one("a[href^='http']:not([href*='google.com'])")
    if site_link:
        data["website"] = site_link.get("href", "")

    return data


def _extract_organic_fields(block) -> dict:
    data = {
        "name": "",
        "address": "",
        "phone": "",
        "website": "",
        "rating": None,
        "email": "",
    }

    title_el = block.select_one("h3")
    if title_el:
        data["name"] = title_el.get_text(strip=True)

    cite_el = block.select_one("cite")
    if cite_el:
        data["website"] = cite_el.get_text(strip=True).split(" ")[0]

    full_text = block.get_text(" ", strip=True)

    phones = extract_phones(full_text)
    if phones:
        data["phone"] = phones[0]

    emails = extract_emails(full_text)
    if emails:
        data["email"] = emails[0]

    addr_match = re.search(
        r"\d+\s+[\w\s]+(?:street|st\.?|avenue|ave\.?|road|rd\.?|lane|ln\.?|"
        r"boulevard|blvd\.?|drive|dr\.?|court|ct\.?)[\w\s,\.]*",
        full_text,
        re.IGNORECASE,
    )
    if addr_match:
        data["address"] = addr_match.group(0).strip()[:120]

    return data


CONTACT_PAGE_PATHS = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/get-in-touch",
]


def _process_batch(
    batch: list[dict],
    task_id: str,
    keyword: str,
    task_logger: logging.Logger,
) -> int:
    saved = 0
    session = RequestSession()

    try:
        for raw in batch:
            raw["source"] = "maps"
            raw["keyword"] = keyword

            # Visit website to extract emails AND phone numbers
            website = raw.get("website", "").strip()
            if website:
                if not website.startswith(("http://", "https://")):
                    website = "https://" + website
                raw["website"] = website
                if not raw.get("email") or not raw.get("phone"):
                    _extract_contacts_from_website(raw, website, session, task_logger)

            enriched = parse_maps_listing(raw)
            cleaned = clean_lead(enriched)

            if not any([cleaned["name"], cleaned["phone"], cleaned["email"]]):
                task_logger.debug(f"Skipping blank record: {raw.get('name', '?')}")
                continue

            row_id = insert_lead(task_id=task_id, **cleaned)
            if row_id:
                saved += 1
                task_logger.debug(
                    f"Saved #{row_id}: '{cleaned['name']}' | "
                    f"phone={cleaned['phone'] or '-'} | email={cleaned['email'] or '-'}"
                )
            else:
                task_logger.debug(f"Duplicate skipped: '{cleaned['name']}'")

    finally:
        session.close()

    return saved


def _extract_contacts_from_website(
    raw: dict,
    website: str,
    session: RequestSession,
    task_logger: logging.Logger,
) -> None:
    """Visit a business website and extract emails AND phone numbers from it."""
    contacts = {
        "emails": [],
        "phones": [],
        "name": "",
        "address": "",
        "social_links": [],
    }

    # Try main page first — most sites put contact info in footer/header
    task_logger.info(f"Fetching homepage: {website}")
    html = _fetch_safe(website, session, task_logger)
    if html:
        html_len = len(html)
        task_logger.info(f"Homepage fetched: {html_len} bytes")
        _merge_contacts(contacts, parse_page_contacts(html, source_url=website))
        task_logger.info(
            f"After homepage: {len(contacts['emails'])} email(s), {len(contacts['phones'])} phone(s)"
        )
    else:
        task_logger.warning(f"Failed to fetch homepage: {website}")

    # If missing email OR phone, try only the most likely contact pages
    if not contacts["emails"] or not contacts["phones"]:
        domain = _extract_domain(website)
        if domain:
            for path in CONTACT_PAGE_PATHS:
                # Stop as soon as we have both
                if contacts["emails"] and contacts["phones"]:
                    break

                sub_url = f"https://{domain}{path}"
                if sub_url == website:
                    continue

                task_logger.debug(f"Trying contact page: {sub_url}")
                sub_html = _fetch_safe(sub_url, session, task_logger)
                if sub_html:
                    _merge_contacts(
                        contacts, parse_page_contacts(sub_html, source_url=sub_url)
                    )
                    task_logger.info(
                        f"After {path}: {len(contacts['emails'])} email(s), {len(contacts['phones'])} phone(s)"
                    )
                else:
                    task_logger.debug(f"Failed to fetch: {sub_url}")

                # Short delay between sub-page fetches
                random_delay()

    # Apply found contacts to raw data
    if contacts["emails"]:
        raw["email"] = contacts["emails"][0]
        task_logger.info(f"Found email: {contacts['emails'][0]}")
    else:
        task_logger.warning(f"No email found for {website}")

    if contacts["phones"]:
        raw["phone"] = contacts["phones"][0]
        task_logger.info(f"Found phone: {contacts['phones'][0]}")
    else:
        task_logger.warning(f"No phone found for {website}")

    if contacts["name"] and not raw.get("name"):
        raw["name"] = contacts["name"]

    if contacts.get("social_links"):
        raw["social_links"] = contacts["social_links"]


def _fetch_safe(
    url: str, session: RequestSession, task_logger: logging.Logger
) -> str | None:
    """Safely fetch a URL and return HTML content."""
    try:
        return session.get(url, timeout=ENRICHER_TIMEOUT)
    except (CaptchaError, BlockedError):
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


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _merge_contacts(target: dict, source: dict) -> None:
    """Merge contact info from source into target."""
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

    for link in source.get("social_links", []):
        if link not in target["social_links"]:
            target["social_links"].append(link)
