import logging
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

from core.config import BATCH_SIZE, REQUEST_TIMEOUT
from database.models import insert_lead, update_task_status
from parser.extractor import (
    extract_phones,
    extract_emails,
    normalize_rating,
    parse_maps_listing,
)
from processing.cleaner import clean_lead
from utils.helpers import get_random_headers, random_delay, retry
from utils.logger import get_logger

logger = get_logger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"


def run_maps_scrape(
    task_id: str,
    task_logger: logging.Logger,
    keyword: str = "",
    location: str = "",
    max_results: int = 20,
    **kwargs,
) -> None:

    task_logger.info(
        f"Maps scraper started | keyword='{keyword}' | location='{location}' | max={max_results}"
    )
    update_task_status(task_id, status="running", progress=0, total=max_results)

    query = f"{keyword} {location}".strip()
    collected = 0

    try:
        raw_listings = _fetch_all_listings(query, max_results, task_logger)
        task_logger.info(f"Fetched {len(raw_listings)} raw listing blocks total")

        batch = []
        for raw in raw_listings:
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
                task_logger.info(
                    f"Batch done | saved={saved} | running_total={collected}"
                )
                batch.clear()
                random_delay()

            if collected >= max_results:
                break

        # Flush the final partial batch
        if batch and collected < max_results:
            saved = _process_batch(batch, task_id, keyword, task_logger)
            collected += saved
            batch.clear()

    except Exception as exc:
        task_logger.error(f"Maps scraper error: {exc}")
        raise

    task_logger.info(f"Maps scrape complete | total leads saved: {collected}")
    update_task_status(
        task_id,
        status="completed",
        progress=collected,
        total=collected,
    )


def _fetch_all_listings(
    query: str,
    max_results: int,
    task_logger: logging.Logger,
) -> list[dict]:

    all_listings: list[dict] = []
    start = 0
    per_page = 10

    while len(all_listings) < max_results:
        params = {
            "q": query,
            "num": per_page,
            "start": start,
            "hl": "en",
            "gl": "us",
        }
        url = f"{GOOGLE_SEARCH_URL}?{urlencode(params)}"
        task_logger.info(f"GET page start={start} → {url}")

        try:
            html = _fetch_page(url)
        except Exception as exc:
            task_logger.warning(f"Page fetch failed (start={start}): {exc}")
            break

        page_listings = _parse_page(html)
        if not page_listings:
            task_logger.info("No listings on this page — ending pagination.")
            break

        all_listings.extend(page_listings)
        task_logger.info(f"Page start={start} → {len(page_listings)} listings")

        if len(page_listings) < per_page:
            break  # Google returned a short page — no more results

        start += per_page
        random_delay()

    return all_listings[:max_results]


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def _fetch_page(url: str) -> str:
    headers = get_random_headers()
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _parse_page(html: str) -> list[dict]:

    soup = BeautifulSoup(html, "lxml")
    listings = _parse_local_cards(soup)
    if listings:
        return listings
    return _parse_organic_blocks(soup)


def _parse_local_cards(soup: BeautifulSoup) -> list[dict]:

    listings = []

    # Google renders local pack results in several container patterns depending
    # on the query and the A/B test variant served. We try them all.
    card_selectors = [
        "div.VkpGBb",
        "div.rllt__details",
        "div[data-cid]",
        "div.uMdZh",
        "div.cXedhc",
    ]

    cards = []
    for selector in card_selectors:
        found = soup.select(selector)
        if found:
            cards = found
            break

    for card in cards:
        listing = _extract_card_fields(card)
        if listing.get("name"):
            listings.append(listing)

    return listings


def _parse_organic_blocks(soup: BeautifulSoup) -> list[dict]:

    listings = []
    blocks = soup.select("div.g, div.tF2Cxc")

    for block in blocks:
        listing = _extract_organic_fields(block)
        if any([listing.get("name"), listing.get("phone"), listing.get("email")]):
            listings.append(listing)

    return listings


def _extract_card_fields(card) -> dict:
    data = {"name": "", "address": "", "phone": "", "website": "", "rating": None}

    # Name
    for selector in [
        "span.OSrXXb",
        "div.dbg0pd span",
        "[role='heading']",
        "h3",
        "span[aria-label]",
    ]:
        el = card.select_one(selector)
        if el:
            data["name"] = el.get_text(strip=True)
            break

    # Address
    for selector in [
        "span.rllt__wrapped",
        "div.rllt__details > div:nth-child(2)",
        "span.LrzXr",
    ]:
        el = card.select_one(selector)
        if el:
            data["address"] = el.get_text(strip=True)
            break

    # Rating — aria-label like "Rated 4.5 out of 5"
    rating_el = card.select_one(
        "span[aria-label*='Rated'], span[aria-label*='stars'], span.Aq14fc"
    )
    if rating_el:
        aria = rating_el.get("aria-label", "")
        match = re.search(r"(\d+\.?\d*)", aria)
        data["rating"] = normalize_rating(
            match.group(1) if match else rating_el.get_text(strip=True)
        )

    # Phone — prefer tel: link, fall back to regex on card text
    tel_link = card.select_one("a[href^='tel:']")
    if tel_link:
        data["phone"] = tel_link["href"].replace("tel:", "").strip()
    else:
        phones = extract_phones(card.get_text(" ", strip=True))
        if phones:
            data["phone"] = phones[0]

    # Website — any external link on the card
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
        raw_url = cite_el.get_text(strip=True).split(" ")[0]
        data["website"] = raw_url

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


def _process_batch(
    batch: list[dict],
    task_id: str,
    keyword: str,
    task_logger: logging.Logger,
) -> int:

    saved = 0
    for raw in batch:
        raw["source"] = "maps"
        raw["keyword"] = keyword

        enriched = parse_maps_listing(raw)
        cleaned = clean_lead(enriched)

        # Skip records with zero usable data
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

    return saved
