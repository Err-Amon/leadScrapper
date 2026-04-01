from typing import Optional
from database.db import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_lead(
    task_id: str,
    name: str = "",
    phone: str = "",
    email: str = "",
    website: str = "",
    address: str = "",
    rating: Optional[float] = None,
    source: str = "unknown",
    keyword: str = "",
) -> Optional[int]:
    if email or phone:
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM leads
                WHERE task_id = ?
                  AND (
                        (email != '' AND email IS NOT NULL AND email = ?)
                     OR (phone != '' AND phone IS NOT NULL AND phone = ?)
                      )
                LIMIT 1
                """,
                (task_id, email or "", phone or ""),
            ).fetchone()
            if existing:
                return None

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads
                (task_id, name, phone, email, website, address, rating, source, keyword)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, name, phone, email, website, address, rating, source, keyword),
        )
        conn.commit()
        return cursor.lastrowid


def get_leads_by_task(
    task_id: str,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    source_filter: str = "",
    has_email: bool = False,
    has_phone: bool = False,
) -> tuple[list[dict], int]:

    conditions, params = _build_filter_conditions(
        task_id, search, source_filter, has_email, has_phone
    )
    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM leads WHERE {where}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"""
            SELECT id, name, phone, email, website, address,
                   rating, source, keyword, enriched, social_links, created_at
            FROM leads
            WHERE {where}
            ORDER BY id ASC
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset],
        ).fetchall()

    return [dict(row) for row in rows], total


def get_task_lead_count(task_id: str) -> int:
    with get_connection() as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE task_id = ?", (task_id,)
        ).fetchone()
    return result[0] if result else 0


def get_leads_missing_email(task_id: str, limit: int = 50) -> list[dict]:

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, website, address, phone
            FROM leads
            WHERE task_id  = ?
              AND enriched  = 0
              AND (email IS NULL OR email = '')
              AND website IS NOT NULL AND website != ''
            ORDER BY id ASC
            LIMIT ?
            """,
            (task_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def iter_leads_for_export(
    task_id: str,
    chunk_size: int = 100,
    search: str = "",
    source_filter: str = "",
    has_email: bool = False,
    has_phone: bool = False,
):
    conditions, base_params = _build_filter_conditions(
        task_id, search, source_filter, has_email, has_phone
    )
    where = " AND ".join(conditions)
    offset = 0

    while True:
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT name, phone, email, website, address,
                       rating, source, keyword, social_links, created_at
                FROM leads
                WHERE {where}
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                base_params + [chunk_size, offset],
            ).fetchall()

        if not rows:
            break

        for row in rows:
            yield dict(row)

        offset += chunk_size


def update_lead_enriched(
    lead_id: int,
    email: str = "",
    phone: str = "",
    social_links: str = "",
) -> None:
    with get_connection() as conn:
        # Fetch current values so we don't overwrite existing data
        current = conn.execute(
            "SELECT email, phone FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()

        if not current:
            return

        new_email = email if (email and not current["email"]) else current["email"]
        new_phone = phone if (phone and not current["phone"]) else current["phone"]

        conn.execute(
            """
            UPDATE leads
            SET email        = ?,
                phone        = ?,
                social_links = ?,
                enriched     = 1,
                enriched_at  = datetime('now')
            WHERE id = ?
            """,
            (new_email, new_phone, social_links or "", lead_id),
        )
        conn.commit()


def update_lead_email(lead_id: int, email: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE leads SET email = ? WHERE id = ?", (email, lead_id))
        conn.commit()


def create_task(
    task_id: str,
    source: str,
    keyword: str = "",
    location: str = "",
    dork_query: str = "",
    max_results: int = 20,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks
                (id, status, source, keyword, location, dork_query, max_results)
            VALUES (?, 'pending', ?, ?, ?, ?, ?)
            """,
            (task_id, source, keyword, location, dork_query, max_results),
        )
        conn.commit()


def update_task_status(
    task_id: str,
    status: str,
    progress: int = 0,
    total: int = 0,
    error: str = "",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status     = ?,
                progress   = ?,
                total      = ?,
                error      = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (status, progress, total, error or None, task_id),
        )
        conn.commit()


def update_task_enrichment_status(task_id: str, enrichment_status: str) -> None:

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET enrichment_status = ?,
                updated_at        = datetime('now')
            WHERE id = ?
            """,
            (enrichment_status, task_id),
        )
        conn.commit()


def get_task(task_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def get_all_tasks(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def _build_filter_conditions(
    task_id: str,
    search: str,
    source_filter: str,
    has_email: bool,
    has_phone: bool,
) -> tuple[list[str], list]:

    conditions: list[str] = ["task_id = ?"]
    params: list = [task_id]

    if search:
        conditions.append(
            "(name LIKE ? OR email LIKE ? OR phone LIKE ? "
            "OR address LIKE ? OR website LIKE ?)"
        )
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    if source_filter in ("maps", "dorks"):
        conditions.append("source = ?")
        params.append(source_filter)

    if has_email:
        conditions.append("email IS NOT NULL AND email != ''")

    if has_phone:
        conditions.append("phone IS NOT NULL AND phone != ''")

    return conditions, params
