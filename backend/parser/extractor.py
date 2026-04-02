import re
import json
from typing import Optional
from bs4 import BeautifulSoup


# Email: standard RFC-5321 subset — broad enough to catch real addresses
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Obfuscated email patterns: info[at]domain.com, info (at) domain . com, etc.
OBFUSCATED_EMAIL_RE = re.compile(
    r"([a-zA-Z0-9._%+\-]+)"
    r"\s*(?:\[at\]|\(at\)|\{at\}|\bat\b|@)"
    r"\s*([a-zA-Z0-9.\-]+)"
    r"\s*(?:\[dot\]|\(dot\)|\{dot\}|\bdot\b|\.)"
    r"\s*([a-zA-Z]{2,})"
)

# Obfuscated email patterns: info[at]domain.com, info (at) domain . com, etc.
OBFUSCATED_EMAIL_RE = re.compile(
    r"([a-zA-Z0-9._%+\-]+)"
    r"\s*(?:\[at\]|\(at\)|\{at\}|\bat\b|@)"
    r"\s*([a-zA-Z0-9.\-]+)"
    r"\s*(?:\[dot\]|\(dot\)|\{dot\}|\bdot\b|\.)"
    r"\s*([a-zA-Z]{2,})"
)

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

# Social media platforms to extract
SOCIAL_PATTERNS = [
    (
        re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/company/[\w\-]+", re.I),
        "linkedin",
    ),
    (
        re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", re.I),
        "linkedin_profile",
    ),
    (re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/[\w\-]+", re.I), "facebook"),
    (re.compile(r"(?:https?://)?(?:www\.)?twitter\.com/[\w\-]+", re.I), "twitter"),
    (re.compile(r"(?:https?://)?(?:www\.)?x\.com/[\w\-]+", re.I), "x_twitter"),
    (re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/[\w\-]+", re.I), "instagram"),
    (re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/[\w\-]+", re.I), "youtube"),
    (re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/[\w\-]+", re.I), "tiktok"),
    (re.compile(r"(?:https?://)?(?:www\.)?pinterest\.com/[\w\-]+", re.I), "pinterest"),
    (re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", re.I), "github"),
    (re.compile(r"(?:https?://)?(?:www\.)?threads\.net/[\w\-]+", re.I), "threads"),
]


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

    # Also try to find obfuscated emails
    for match in OBFUSCATED_EMAIL_RE.finditer(text):
        user = match.group(1).strip().lower()
        host = match.group(2).strip().lower()
        tld = match.group(3).strip().lower()
        email = f"{user}@{host}.{tld}"

        if email not in seen:
            domain = host + "." + tld
            if domain not in JUNK_EMAIL_DOMAINS and len(email) <= 80:
                seen[email] = None

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

    # Also try to find standalone phone-like number sequences
    standalone_phones = re.findall(r"\+?[\d][\d\s\-\(\)]{6,}", text)
    for sp in standalone_phones:
        cleaned = sp.strip()
        digits = re.sub(r"\D", "", cleaned)
        if 7 <= len(digits) <= 15 and digits not in seen:
            seen[digits] = cleaned

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
        "social_links": raw.get("social_links", []),
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
        return {
            "emails": [],
            "phones": [],
            "name": "",
            "address": "",
            "social_links": [],
        }

    soup = BeautifulSoup(html, "lxml")

    # Extract from JSON-LD structured data FIRST (before removing scripts)
    json_emails, json_phones, json_addr = _extract_json_ld_contacts(soup)

    # Extract emails from ALL href attributes before removing anything
    emails = []

    # 1. mailto: links (most reliable)
    for a_tag in soup.select("a[href^='mailto:']"):
        href = a_tag["href"].replace("mailto:", "").split("?")[0].strip().lower()
        if href and "@" in href:
            emails.append(href)

    # 2. Any href containing @ or mailto (obfuscated, encoded, etc.)
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if "mailto" in href.lower() or "@" in href:
            mail_match = EMAIL_RE.search(href)
            if mail_match:
                email = mail_match.group(0).strip().lower().rstrip(".,;)")
                if email not in emails:
                    emails.append(email)

    # 3. Check meta tags for emails (description, keywords, author, etc.)
    for meta in soup.find_all("meta"):
        for attr_name in ["content", "value"]:
            content = meta.get(attr_name, "")
            if content and "@" in content:
                for match in EMAIL_RE.findall(content):
                    email = match.strip().lower().rstrip(".,;)")
                    if email and email not in emails:
                        emails.append(email)

    # 4. Check all attribute values for email patterns (data-email, data-contact, etc.)
    for tag in soup.find_all(True):
        for attr_name, attr_value in tag.attrs.items():
            if isinstance(attr_value, str) and "@" in attr_value:
                for match in EMAIL_RE.findall(attr_value):
                    email = match.strip().lower().rstrip(".,;)")
                    if email and email not in emails:
                        emails.append(email)
            elif isinstance(attr_value, list):
                for val in attr_value:
                    if "@" in val:
                        for match in EMAIL_RE.findall(val):
                            email = match.strip().lower().rstrip(".,;)")
                            if email and email not in emails:
                                emails.append(email)

    # Now remove script/style/noscript — they're not useful for visible text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    full_text = soup.get_text(" ", strip=True)

    # 5. Extract emails from visible page text
    emails.extend(extract_emails(full_text))
    emails.extend(json_emails)
    emails = list(dict.fromkeys(emails))  # dedup, preserve order

    # Phones
    phones = []

    # 1. tel: links (most reliable)
    for a_tag in soup.select("a[href^='tel:']"):
        href = a_tag["href"].replace("tel:", "").strip()
        digits = re.sub(r"\D", "", href)
        if 7 <= len(digits) <= 15:
            phones.append(href)

    # 2. Check all href attributes for phone patterns (callto:, wtsp:, whatsapp:, phone:, sms:)
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if any(
            p in href.lower()
            for p in ["tel:", "callto:", "wtsp:", "whatsapp:", "phone:", "sms:"]
        ):
            phone_match = re.search(r"[\d\+\-\(\)\s]{7,20}", href)
            if phone_match:
                phone = phone_match.group(0).strip()
                digits = re.sub(r"\D", "", phone)
                if 7 <= len(digits) <= 15 and phone not in phones:
                    phones.append(phone)

    # 3. Check meta tags for phone numbers
    for meta in soup.find_all("meta"):
        for attr_name in ["content", "value"]:
            content = meta.get(attr_name, "")
            if content:
                phone_matches = extract_phones(content)
                for p in phone_matches:
                    if p not in phones:
                        phones.append(p)

    # 4. Check all attribute values for phone patterns (data-phone, data-tel, data-contact, etc.)
    for tag in soup.find_all(True):
        for attr_name, attr_value in tag.attrs.items():
            if isinstance(attr_value, str):
                # Check for tel: in href-like attributes
                if "tel:" in attr_value.lower() or re.search(r"[\d]{7,}", attr_value):
                    phone_matches = extract_phones(attr_value)
                    for p in phone_matches:
                        if p not in phones:
                            phones.append(p)
            elif isinstance(attr_value, list):
                for val in attr_value:
                    if "tel:" in val.lower() or re.search(r"[\d]{7,}", val):
                        phone_matches = extract_phones(val)
                        for p in phone_matches:
                            if p not in phones:
                                phones.append(p)

    # 5. Extract phones from visible page text
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

    # Social links
    social_links = _extract_social_links(soup)

    return {
        "emails": emails[:5],
        "phones": phones[:3],
        "name": name[:120],
        "address": address[:150],
        "social_links": social_links,
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


def _extract_social_links(soup: BeautifulSoup) -> list[str]:
    """Extract social media profile URLs from parsed HTML."""
    found: dict[str, str] = {}

    # 1. Check all href attributes (absolute and relative URLs)
    for a_tag in soup.select("a[href]"):
        href = a_tag["href"].strip()
        # Normalize relative URLs to absolute by prepending a dummy domain
        test_href = href if href.startswith("http") else "https://example.com" + href
        for pattern, platform in SOCIAL_PATTERNS:
            if platform not in found:
                match = pattern.search(test_href)
                if match:
                    cleaned = match.group(0)
                    if not cleaned.startswith("http"):
                        cleaned = "https://" + cleaned
                    found[platform] = cleaned

    # 2. Check aria-label attributes on links/icons
    for tag in soup.find_all(True):
        aria = tag.get("aria-label", "")
        if aria:
            aria_lower = aria.lower()
            for platform_key in [
                "linkedin",
                "facebook",
                "twitter",
                "instagram",
                "youtube",
                "tiktok",
                "pinterest",
                "github",
                "threads",
            ]:
                if platform_key in aria_lower and platform_key not in found:
                    # Try to find the URL from parent <a> tag
                    parent_a = tag.find_parent("a")
                    if parent_a and parent_a.get("href"):
                        parent_href = parent_a["href"].strip()
                        test_href = (
                            parent_href
                            if parent_href.startswith("http")
                            else "https://example.com" + parent_href
                        )
                        for pattern, platform in SOCIAL_PATTERNS:
                            if platform == platform_key or platform.startswith(
                                platform_key
                            ):
                                match = pattern.search(test_href)
                                if match:
                                    cleaned = match.group(0)
                                    if not cleaned.startswith("http"):
                                        cleaned = "https://" + cleaned
                                    found[platform] = cleaned
                                    break
                        if platform_key in [p for p in found]:
                            break

    # 3. Check for social links in JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json

            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    for key in ["sameAs", "socialLinks"]:
                        links = item.get(key, [])
                        if isinstance(links, list):
                            for link in links:
                                if isinstance(link, str):
                                    for pattern, platform in SOCIAL_PATTERNS:
                                        if platform not in found:
                                            match = pattern.search(link)
                                            if match:
                                                cleaned = match.group(0)
                                                if not cleaned.startswith("http"):
                                                    cleaned = "https://" + cleaned
                                                found[platform] = cleaned
                        elif isinstance(links, str):
                            for pattern, platform in SOCIAL_PATTERNS:
                                if platform not in found:
                                    match = pattern.search(links)
                                    if match:
                                        cleaned = match.group(0)
                                        if not cleaned.startswith("http"):
                                            cleaned = "https://" + cleaned
                                        found[platform] = cleaned
        except Exception:
            pass

    return list(found.values())
