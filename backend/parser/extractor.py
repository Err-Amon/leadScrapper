import re
from typing import Optional

# Email pattern: broad but filters obvious junk
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Phone: matches common international + local formats
PHONE_RE = re.compile(r"(\+?[\d\s\-().]{7,20})")

JUNK_EMAIL_DOMAINS = {"example.com", "test.com", "domain.com", "email.com"}


def extract_emails(text: str) -> list[str]:
    matches = EMAIL_RE.findall(text)
    cleaned = []
    for email in matches:
        email = email.strip().lower()
        domain = email.split("@")[-1]
        if domain not in JUNK_EMAIL_DOMAINS:
            cleaned.append(email)
    return list(dict.fromkeys(cleaned))  # Deduplicate, preserve order


def extract_phones(text: str) -> list[str]:
    matches = PHONE_RE.findall(text)
    cleaned = []
    for phone in matches:
        phone = phone.strip()
        digits = re.sub(r"\D", "", phone)
        if 7 <= len(digits) <= 15:
            cleaned.append(phone)
    return list(dict.fromkeys(cleaned))


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"[^\d+]", "", phone)
    return digits


def normalize_rating(raw: str) -> Optional[float]:
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None
