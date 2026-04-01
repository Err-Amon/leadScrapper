import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config import EXPORTS_DIR, EXPORT_CHUNK_SIZE
from database.models import iter_leads_for_export, get_task
from utils.logger import get_logger

logger = get_logger(__name__)

# Column order in every exported CSV
CSV_COLUMNS = [
    "name",
    "phone",
    "email",
    "website",
    "address",
    "rating",
    "source",
    "keyword",
    "created_at",
]


def generate_csv(
    task_id: str,
    search: str = "",
    source_filter: str = "",
    has_email: bool = False,
    has_phone: bool = False,
) -> Path:

    task = get_task(task_id)
    if not task:
        raise RuntimeError(f"Task {task_id} not found — cannot export.")

    filename = _build_filename(task, source_filter)
    out_path = EXPORTS_DIR / filename

    logger.info(f"Starting CSV export | task={task_id} | file={filename}")

    row_count = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore",  # silently drop any extra keys
        )
        writer.writeheader()

        for lead in iter_leads_for_export(
            task_id,
            chunk_size=EXPORT_CHUNK_SIZE,
            search=search,
            source_filter=source_filter,
            has_email=has_email,
            has_phone=has_phone,
        ):
            writer.writerow(lead)
            row_count += 1

    logger.info(f"CSV export complete | {row_count} rows → {out_path}")
    return out_path


def _build_filename(task: dict, source_filter: str) -> str:

    parts = ["leads"]

    # Keyword from Maps task, or first two words of dork query
    keyword = task.get("keyword") or ""
    dork = task.get("dork_query") or ""
    location = task.get("location") or ""

    if keyword:
        parts.append(_slugify(keyword))
    elif dork:
        # Use first two words of the dork query as a slug
        words = dork.strip().split()[:2]
        parts.append(_slugify(" ".join(words)))

    if location:
        parts.append(_slugify(location))

    # Source — use filter if applied, otherwise use the task's source
    effective_source = source_filter or task.get("source", "")
    if effective_source:
        parts.append(effective_source)

    parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))

    return "_".join(parts) + ".csv"


def _slugify(text: str, max_len: int = 30) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s\-]+", "_", text)
    return text[:max_len].strip("_")
