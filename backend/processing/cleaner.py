import re
from typing import Optional
from parser.extractor import normalize_phone


def clean_lead(raw: dict) -> dict:

    return {
        "name": _clean_text(raw.get("name", "")),
        "phone": normalize_phone(raw.get("phone", "")),
        "email": _clean_email(raw.get("email", "")),
        "website": _clean_url(raw.get("website", "")),
        "address": _clean_text(raw.get("address", "")),
        "rating": _clean_rating(raw.get("rating")),
        "source": raw.get("source", "unknown"),
        "keyword": _clean_text(raw.get("keyword", "")),
    }


def _clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())  # Collapse whitespace


def _clean_email(email: str) -> str:
    if not email:
        return ""
    email = email.strip().lower()
    # Basic sanity check
    if "@" not in email or "." not in email.split("@")[-1]:
        return ""
    return email


def _clean_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _clean_rating(raw) -> Optional[float]:
    if raw is None:
        return None
    try:
        value = float(str(raw).replace(",", "."))
        return round(value, 1) if 0.0 <= value <= 5.0 else None
    except (ValueError, TypeError):
        return None
