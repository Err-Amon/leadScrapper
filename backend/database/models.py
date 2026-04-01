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

    # Deduplication check within the same task
    if email or phone:
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM leads
                WHERE task_id = ?
                  AND (
                        (email != '' AND email = ?)
                     OR (phone != '' AND phone = ?)
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
            INSERT INTO leads (task_id, name, phone, email, website, address, rating, source, keyword)
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
) -> tuple[list[dict], int]:

    offset = (page - 1) * page_size
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE task_id = ?",
            (task_id,),
        ).fetchone()[0]

        rows = conn.execute(
            """
            SELECT id, name, phone, email, website, address, rating, source, keyword, created_at
            FROM leads
            WHERE task_id = ?
            ORDER BY id ASC
            LIMIT ? OFFSET ?
            """,
            (task_id, page_size, offset),
        ).fetchall()

    leads = [dict(row) for row in rows]
    return leads, total


def iter_leads_for_export(task_id: str, chunk_size: int = 100):

    offset = 0
    while True:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT name, phone, email, website, address, rating, source, keyword, created_at
                FROM leads
                WHERE task_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (task_id, chunk_size, offset),
            ).fetchall()

        if not rows:
            break

        for row in rows:
            yield dict(row)

        offset += chunk_size


def update_lead_email(lead_id: int, email: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE leads SET email = ? WHERE id = ?",
            (email, lead_id),
        )
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
            INSERT INTO tasks (id, status, source, keyword, location, dork_query, max_results)
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
            SET status = ?, progress = ?, total = ?, error = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (status, progress, total, error or None, task_id),
        )
        conn.commit()


def get_task(task_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    if row:
        task = dict(row)
        task["task_id"] = task.pop("id")
        return task
    return None


def get_all_tasks(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    tasks = []
    for row in rows:
        task = dict(row)
        task["task_id"] = task.pop("id")
        tasks.append(task)
    return tasks
