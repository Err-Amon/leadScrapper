import logging
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

from core.config import (
    ENRICHER_MAX_PAGES_PER_DOMAIN,
    ENRICHER_TIMEOUT,
    ENRICHER_MAX_CONCURRENT,
)
from database.models import (
    get_leads_missing_email,
    update_lead_enriched,
    update_task_enrichment_status,
)
from parser.extractor import parse_page_contacts
from processing.cleaner import _clean_email, _clean_phone
from utils.helpers import get_random_headers, random_delay
from utils.logger import get_logger

logger = get_logger(__name__)

# Sub-page paths to check when root page yields no email
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/reach-us",
    "/get-in-touch",
]

# Social domains we actively look for in href attributes
SOCIAL_DOMAINS = {
    "facebook.com": "facebook",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "tiktok.com": "tiktok",
    "pinterest.com": "pinterest",
}

# How many leads to pull from DB per enrichment cycle
ENRICHMENT_BATCH_SIZE = 20


def run_enrichment(
    task_id: str,
    task_logger: logging.Logger,
    **kwargs,
) -> None:
    task_logger.info(f"Enrichment started for task {task_id}")
    update_task_enrichment_status(task_id, "running")

    total_enriched = 0
    total_attempted = 0

    try:
        while True:
            # Pull the next batch of candidates from the DB
            candidates = get_leads_missing_email(task_id, limit=ENRICHMENT_BATCH_SIZE)

            if not candidates:
                task_logger.info("No more enrichment candidates — done.")
                break

            task_logger.info(f"Enrichment batch: {len(candidates)} leads to process")

            results = _enrich_batch_concurrent(candidates, task_logger)

            for lead_id, enriched_data in results.items():
                total_attempted += 1
                if enriched_data:
                    update_lead_enriched(
                        lead_id=lead_id,
                        email=enriched_data.get("email", ""),
                        phone=enriched_data.get("phone", ""),
                        social_links=enriched_data.get("social_links", ""),
                    )
                    total_enriched += 1
                    task_logger.debug(
                        f"Lead #{lead_id} enriched: "
                        f"email={enriched_data.get('email') or '-'} "
                        f"phone={enriched_data.get('phone') or '-'} "
                        f"socials={enriched_data.get('social_links') or '-'}"
                    )
                else:
                    # Mark as enriched even with no data found —
                    # prevents infinite re-processing of unreachable sites
                    update_lead_enriched(lead_id=lead_id)
                    task_logger.debug(f"Lead #{lead_id}: no data found, marked done")

            task_logger.info(
                f"Batch complete | enriched={total_enriched}/{total_attempted}"
            )
            random_delay()

    except Exception as exc:
        task_logger.error(f"Enrichment failed: {exc}")
        update_task_enrichment_status(task_id, "failed")
        raise

    task_logger.info(
        f"Enrichment complete | "
        f"total_enriched={total_enriched} / total_attempted={total_attempted}"
    )
    update_task_enrichment_status(task_id, "completed")


def _enrich_batch_concurrent(
    candidates: list[dict],
    task_logger: logging.Logger,
) -> dict[int, dict | None]:
    results: dict[int, dict | None] = {}

    with ThreadPoolExecutor(
        max_workers=ENRICHER_MAX_CONCURRENT,
        thread_name_prefix="enricher",
    ) as pool:
        future_to_lead = {
            pool.submit(_enrich_single_lead, lead, task_logger): lead["id"]
            for lead in candidates
        }

        for future in as_completed(future_to_lead):
            lead_id = future_to_lead[future]
            try:
                results[lead_id] = future.result()
            except Exception as exc:
                task_logger.warning(
                    f"Enrichment worker error for lead #{lead_id}: {exc}"
                )
                results[lead_id] = None

    return results


def _enrich_single_lead(
    lead: dict,
    task_logger: logging.Logger,
) -> dict | None:
    website = lead.get("website", "").strip()
    if not website:
        return None

    domain = _extract_domain(website)
    if not domain:
        return None

    task_logger.debug(f"Enriching lead #{lead['id']}: {website}")

    aggregated = {
        "emails": [],
        "phones": [],
        "social_links": [],
    }

    pages_visited = 0

    # Build the ordered list of pages to visit:
    # root URL first, then contact/about sub-pages
    pages_to_visit = [website] + [f"https://{domain}{path}" for path in CONTACT_PATHS]

    for page_url in pages_to_visit:
        if pages_visited >= ENRICHER_MAX_PAGES_PER_DOMAIN:
            break

        html = _fetch_page(page_url)
        if not html:
            continue

        pages_visited += 1

        # Extract contact data from this page
        page_contacts = parse_page_contacts(html, source_url=page_url)
        _merge_list(aggregated["emails"], page_contacts.get("emails", []))
        _merge_list(aggregated["phones"], page_contacts.get("phones", []))

        # Extract social links from this page's anchor tags
        socials = _extract_social_links(html)
        _merge_list(aggregated["social_links"], socials)

        # Stop visiting more pages once we have an email
        if aggregated["emails"]:
            break

    # Nothing found across all pages
    if not any(
        [aggregated["emails"], aggregated["phones"], aggregated["social_links"]]
    ):
        return None

    # Clean and return the best contact info found
    best_email = _clean_email(aggregated["emails"][0]) if aggregated["emails"] else ""
    best_phone = _clean_phone(aggregated["phones"][0]) if aggregated["phones"] else ""
    social_str = "|".join(aggregated["social_links"][:5])  # Cap at 5 social links

    return {
        "email": best_email,
        "phone": best_phone,
        "social_links": social_str,
    }


def _fetch_page(url: str) -> str | None:
    try:
        headers = get_random_headers()
        response = requests.get(
            url,
            headers=headers,
            timeout=ENRICHER_TIMEOUT,
            allow_redirects=True,
        )
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None
        response.raise_for_status()
        return response.text

    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.TooManyRedirects:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.HTTPError:
        return None
    except Exception:
        return None


def _extract_social_links(html: str) -> list[str]:
    from bs4 import BeautifulSoup

    found: dict[str, str] = {}  # platform → url (keeps first found per platform)

    try:
        soup = BeautifulSoup(html, "lxml")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            # Normalize relative URLs to absolute for matching
            test_href = (
                href if href.startswith("http") else "https://example.com" + href
            )
            for domain, platform in SOCIAL_DOMAINS.items():
                if domain in test_href and platform not in found:
                    # Clean the URL — just scheme + domain + path, no query strings
                    cleaned = _strip_url_query(
                        href
                        if href.startswith("http")
                        else "https://" + href.lstrip("/")
                    )
                    if cleaned:
                        found[platform] = cleaned
    except Exception:
        pass

    return list(found.values())


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _strip_url_query(url: str) -> str:
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    except Exception:
        return url


def _merge_list(target: list, source: list) -> None:
    seen = set(target)
    for item in source:
        if item not in seen:
            target.append(item)
            seen.add(item)
