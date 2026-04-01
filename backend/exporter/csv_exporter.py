import csv
import re
from datetime import datetime
from pathlib import Path

from core.config import EXPORTS_DIR, EXPORT_CHUNK_SIZE
from database.models import iter_leads_for_export, get_task
from utils.logger import get_logger

logger = get_logger(__name__)

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


def generate_csv(task_id: str) -> Path:

    task = get_task(task_id)
    filename = _build_filename(task)
    output_path = EXPORTS_DIR / filename

    logger.info(f"Generating CSV for task {task_id} → {output_path}")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()

        count = 0
        for lead in iter_leads_for_export(task_id, chunk_size=EXPORT_CHUNK_SIZE):
            writer.writerow(lead)
            count += 1

    logger.info(f"CSV export complete: {count} rows written to {output_path}")
    return output_path


def _build_filename(task: dict) -> str:
    parts = ["leads"]
    keyword = task.get("keyword", "") or task.get("dork_query", "") or "export"
    location = task.get("location", "")

    slug = _slugify(keyword)
    if location:
        slug += f"_{_slugify(location)}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{parts[0]}_{slug}_{timestamp}.csv"


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:40]
