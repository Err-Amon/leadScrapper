import re
from typing import Optional


def clean_lead(raw: dict) -> dict:
    return {
        "name": _clean_text(raw.get("name", ""), max_len=120),
        "phone": _clean_phone(raw.get("phone", "")),
        "email": _clean_email(raw.get("email", "")),
        "website": _clean_url(raw.get("website", "")),
        "address": _clean_text(raw.get("address", ""), max_len=200),
        "rating": _clean_rating(raw.get("rating")),
        "source": _clean_text(raw.get("source", "unknown"), max_len=20),
        "keyword": _clean_text(raw.get("keyword", ""), max_len=100),
        "social_links": _clean_social_links(raw.get("social_links", [])),
    }


def _clean_text(value, max_len: int = 255) -> str:
    if not value:
        return ""
    cleaned = " ".join(str(value).split())
    return cleaned[:max_len]


def _clean_phone(phone: str) -> str:
    if not phone:
        return ""

    phone = phone.strip()

    # Preserve leading +
    has_plus = phone.startswith("+")
    digits = re.sub(r"\D", "", phone)

    if not (7 <= len(digits) <= 15):
        return ""

    return ("+" if has_plus else "") + digits


def _clean_email(email: str) -> str:
    if not email:
        return ""

    email = email.strip().lower().rstrip(".,;)")

    # Must have exactly one @
    parts = email.split("@")
    if len(parts) != 2:
        return ""

    local, domain = parts

    # Local and domain both need content
    if not local or not domain:
        return ""

    # Domain must have at least one dot and a valid TLD (2+ chars)
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or len(domain_parts[-1]) < 2:
        return ""

    # Reject known junk / placeholder domains
    junk_domains = frozenset(
        {
            "example.com",
            "test.com",
            "domain.com",
            "email.com",
            "yourdomain.com",
            "sampleemail.com",
            "company.com",
        }
    )
    if domain in junk_domains:
        return ""

    # Overall length sanity check
    if len(email) > 80:
        return ""

    return email


def _clean_url(url: str) -> str:
    if not url:
        return ""

    url = url.strip()

    # Strip common non-URL prefixes that sometimes appear in scraped text
    url = re.sub(r"^(www\.)", "https://\\1", url)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove fragment identifiers and trailing whitespace
    url = url.split("#")[0].strip()

    # Basic sanity: must have a domain with a dot
    try:
        domain_part = url.split("//", 1)[1].split("/")[0]
        if "." not in domain_part:
            return ""
    except IndexError:
        return ""

    return url[:500]


def _clean_rating(raw) -> Optional[float]:
    if raw is None:
        return None
    try:
        value = float(str(raw).replace(",", ".").strip())
        if 0.0 <= value <= 5.0:
            return round(value, 1)
        return None
    except (ValueError, TypeError):
        return None


def _clean_social_links(links) -> str:
    if not links:
        return ""
    if isinstance(links, list):
        seen = set()
        cleaned = []
        for link in links:
            link = link.strip() if isinstance(link, str) else ""
            if link and link not in seen:
                seen.add(link)
                cleaned.append(link)
        return "|".join(cleaned[:5])
    if isinstance(links, str):
        return links.strip()[:500]
    return ""
