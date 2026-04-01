import sqlite3
from contextlib import contextmanager
from core.config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def init_db() -> None:

    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id      TEXT    NOT NULL,
                name         TEXT,
                phone        TEXT,
                email        TEXT,
                website      TEXT,
                address      TEXT,
                rating       REAL,
                source       TEXT    NOT NULL DEFAULT 'unknown',
                keyword      TEXT,
                enriched     INTEGER NOT NULL DEFAULT 0,
                social_links TEXT,
                enriched_at  TEXT,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Migrate existing databases that predate Phase 5 columns
        _add_column_if_missing(conn, "leads", "enriched", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "leads", "social_links", "TEXT")
        _add_column_if_missing(conn, "leads", "enriched_at", "TEXT")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_email
            ON leads (email)
            WHERE email IS NOT NULL AND email != '';
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_phone
            ON leads (phone)
            WHERE phone IS NOT NULL AND phone != '';
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_task_id
            ON leads (task_id);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_enriched
            ON leads (task_id, enriched);
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id               TEXT    PRIMARY KEY,
                status           TEXT    NOT NULL DEFAULT 'pending',
                source           TEXT    NOT NULL,
                keyword          TEXT,
                location         TEXT,
                dork_query       TEXT,
                max_results      INTEGER NOT NULL DEFAULT 20,
                progress         INTEGER NOT NULL DEFAULT 0,
                total            INTEGER NOT NULL DEFAULT 0,
                error            TEXT,
                enrichment_status TEXT   DEFAULT 'none',
                created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)

        _add_column_if_missing(
            conn, "tasks", "enrichment_status", "TEXT DEFAULT 'none'"
        )

        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")


def _add_column_if_missing(conn, table: str, column: str, definition: str) -> None:

    existing = {
        row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
        logger.info(f"Migrated: added column '{column}' to table '{table}'")


@contextmanager
def get_connection():

    conn = sqlite3.connect(str(DB_PATH), timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Rows accessible as dicts
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
