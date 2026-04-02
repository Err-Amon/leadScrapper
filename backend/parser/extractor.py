import re
import json
from typing import Optional
from bs4 import BeautifulSoup


# Email: standard RFC-5321 subset — broad enough to catch real addresses
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Phone: international and local formats
# Matches: +92-300-1234567, (021) 345-6789, 0300 123 4567, +1 800 555-0100
PHONE_RE = re.compile(
    r"(?<!\d)"  # not preceded by digit
    r"(\+?[\d]{1,3}[\s.\-]?)?"  # optional country code
    r"(\(?\d{2,4}\)?[\s.\-]?)"  # area code
    r"(\d{3,4}[\s.\-]?)"  # first segment
    r"(\d{3,4})"  # last segment
    r"(?!\d)"  # not followed by digit
)

# Junk email domains to filter out
JUNK_EMAIL_DOMAINS = frozenset(
    {
        "example.com",
        "test.com",
        "domain.com",
        "email.com",
        "yourdomain.com",
        "company.com",
        "sampleemail.com",
        "w3schools.com",
        "schema.org",
    }
)

# Known image/asset file extensions — filter from email-like patterns
ASSET_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".css",
        ".js",
        ".woff",
        ".ttf",
    }
)


def extract_emails(text: str) -> list[str]:
    if not text:
        return []

    matches = EMAIL_RE.findall(text)
    seen = {}

    for email in matches:
        email = email.strip().lower().rstrip(".,;)")
        if not email or "@" not in email:
            continue

        domain = email.split("@")[-1]

        # Filter junk
        if domain in JUNK_EMAIL_DOMAINS:
            continue
        if any(email.endswith(ext) for ext in ASSET_EXTENSIONS):
            continue
        if len(email) > 80 or len(domain) < 4:
            continue

        seen[email] = None  # OrderedDict-style dedup

    return list(seen.keys())


def extract_phones(text: str) -> list[str]:
    if not text:
        return []

    matches = PHONE_RE.findall(text)
    seen = {}

    for groups in matches:
        phone = "".join(groups).strip()
        digits = re.sub(r"\D", "", phone)

        if not (7 <= len(digits) <= 15):
            continue

        # Normalise to a canonical key for dedup purposes
        key = digits
        if key not in seen:
            seen[key] = phone.strip()

    return list(seen.values())


def normalize_rating(raw) -> Optional[float]:
    if raw is None:
        return None
    try:
        value = float(str(raw).replace(",", ".").strip())
        return round(value, 1) if 0.0 <= value <= 5.0 else None
    except (ValueError, TypeError):
        return None


def parse_maps_listing(raw: dict) -> dict:
    result = {
        "name": raw.get("name", ""),
        "phone": raw.get("phone", ""),
        "email": raw.get("email", ""),
        "website": raw.get("website", ""),
        "address": raw.get("address", ""),
        "rating": raw.get("rating"),
        "source": raw.get("source", "maps"),
        "keyword": raw.get("keyword", ""),
    }

    # If phone is missing, try to extract it from the address string
    if not result["phone"] and result["address"]:
        phones = extract_phones(result["address"])
        if phones:
            result["phone"] = phones[0]

    # If email is missing, try from website field (sometimes pasted as text)
    if not result["email"] and result["website"]:
        emails = extract_emails(result["website"])
        if emails:
            result["email"] = emails[0]
            result["website"] = ""  # It was an email mistaken for a URL

    # Trim name: remove trailing punctuation and excess whitespace
    if result["name"]:
        result["name"] = re.sub(r"[·•|–\-]+$", "", result["name"]).strip()

    # Normalize rating
    result["rating"] = normalize_rating(result["rating"])

    return result


def parse_page_contacts(html: str, source_url: str = "") -> dict:
    if not html:
        return {"emails": [], "phones": [], "name": "", "address": ""}

    soup = BeautifulSoup(html, "lxml")

    # Extract from JSON-LD structured data FIRST (before removing scripts)
    json_emails, json_phones, json_addr = _extract_json_ld_contacts(soup)

    # Remove script and style content — not useful for contact extraction
    for tag in soup(["script", "style", "noscript", "meta", "link"]):
        tag.decompose()

    full_text = soup.get_text(" ", strip=True)

    # Also scan mailto: links — more reliable than regex on rendered text
    emails = []
    for a_tag in soup.select("a[href^='mailto:']"):
        href = a_tag["href"].replace("mailto:", "").split("?")[0].strip().lower()
        if href and "@" in href:
            emails.append(href)

    # Also look for email patterns in hrefs like "mailto:" encoded forms
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if "mailto" in href.lower() or "@" in href:
            mail_match = EMAIL_RE.search(href)
            if mail_match:
                email = mail_match.group(0).strip().lower().rstrip(".,;)")
                if email not in emails:
                    emails.append(email)

    emails.extend(json_emails)
    emails.extend(extract_emails(full_text))
    emails = list(dict.fromkeys(emails))  # dedup, preserve order

    phones = []
    for a_tag in soup.select("a[href^='tel:']"):
        href = a_tag["href"].replace("tel:", "").strip()
        digits = re.sub(r"\D", "", href)
        if 7 <= len(digits) <= 15:
            phones.append(href)

    # Also check for phone patterns in hrefs like "callto:" or "wtsp:"
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if any(
            p in href.lower()
            for p in ["tel:", "callto:", "wtsp:", "whatsapp:", "phone:"]
        ):
            phone_match = re.search(r"[\d\+\-\(\)\s]{7,20}", href)
            if phone_match:
                phone = phone_match.group(0).strip()
                digits = re.sub(r"\D", "", phone)
                if 7 <= len(digits) <= 15 and phone not in phones:
                    phones.append(phone)

    phones.extend(json_phones)
    phones.extend(extract_phones(full_text))
    phones = list(dict.fromkeys(phones))

    name = ""
    og_site = soup.select_one("meta[property='og:site_name']")
    og_title = soup.select_one("meta[property='og:title']")
    title_tag = soup.select_one("title")
    h1_tag = soup.select_one("h1")

    if og_site and og_site.get("content"):
        name = og_site["content"].strip()
    elif h1_tag:
        name = h1_tag.get_text(strip=True)
    elif og_title and og_title.get("content"):
        name = og_title["content"].strip()
    elif title_tag:
        name = title_tag.get_text(strip=True)

    address = json_addr if json_addr else ""
    if not address:
        schema_addr = soup.select_one(
            "[itemprop='streetAddress'], [itemprop='address']"
        )
        if schema_addr:
            address = schema_addr.get_text(strip=True)
        else:
            addr_match = re.search(
                r"\d{1,5}\s+[\w\s]+(?:street|st\.?|avenue|ave\.?|road|rd\.?|lane|ln\.?|"
                r"boulevard|blvd\.?|drive|dr\.?|court|ct\.?)[\w\s,\.]{0,60}",
                full_text,
                re.IGNORECASE,
            )
            if addr_match:
                address = addr_match.group(0).strip()

    return {
        "emails": emails[:5],  # Cap at 5 to avoid spam lists
        "phones": phones[:3],  # Cap at 3 most likely numbers
        "name": name[:120],
        "address": address[:150],
    }


def _extract_json_ld_contacts(soup: BeautifulSoup) -> tuple[list, list, str]:
    """Extract emails, phones, and addresses from JSON-LD structured data."""
    emails: list[str] = []
    phones: list[str] = []
    address = ""

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check for email field directly
                if item.get("email"):
                    email = item["email"].strip().lower()
                    if email and "@" in email and email not in emails:
                        emails.append(email)

                # Check for telephone field
                if item.get("telephone"):
                    phone = item["telephone"].strip()
                    digits = re.sub(r"\D", "", phone)
                    if 7 <= len(digits) <= 15 and phone not in phones:
                        phones.append(phone)

                # Check for faxNumber
                if item.get("faxNumber"):
                    phone = item["faxNumber"].strip()
                    digits = re.sub(r"\D", "", phone)
                    if 7 <= len(digits) <= 15 and phone not in phones:
                        phones.append(phone)

                # Extract from address object
                addr = item.get("address", {})
                if isinstance(addr, dict):
                    parts = [
                        addr.get("streetAddress", ""),
                        addr.get("addressLocality", ""),
                        addr.get("addressRegion", ""),
                        addr.get("postalCode", ""),
                        addr.get("addressCountry", ""),
                    ]
                    addr_str = ", ".join(p for p in parts if p).strip()
                    if addr_str and not address:
                        address = addr_str[:150]

                # Recursively search nested objects for emails/phones
                _recursive_extract(item, emails, phones)

        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    # Also scan raw script text for email/phone patterns that aren't valid JSON
    for script in soup.find_all("script", type="application/ld+json"):
        if script.string:
            email_matches = EMAIL_RE.findall(script.string)
            for e in email_matches:
                e = e.strip().lower().rstrip(".,;)")
                domain = e.split("@")[-1] if "@" in e else ""
                if e and domain not in JUNK_EMAIL_DOMAINS and e not in emails:
                    emails.append(e)

    return emails, phones, address


def _recursive_extract(data, emails: list, phones: list) -> None:
    """Recursively search nested dicts/lists for email and phone patterns."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                if "@" in value:
                    match = EMAIL_RE.search(value)
                    if match:
                        email = match.group(0).strip().lower()
                        domain = email.split("@")[-1]
                        if domain not in JUNK_EMAIL_DOMAINS and email not in emails:
                            emails.append(email)
                digits_in_value = re.sub(r"\D", "", value)
                if 7 <= len(digits_in_value) <= 15 and any(c.isdigit() for c in value):
                    if value not in phones:
                        phones.append(value)
            elif isinstance(value, (dict, list)):
                _recursive_extract(value, emails, phones)
    elif isinstance(data, list):
        for item in data:
            _recursive_extract(item, emails, phones)
