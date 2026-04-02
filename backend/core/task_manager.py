import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, wait as futures_wait, FIRST_COMPLETED
from typing import Callable

from core.config import MAX_WORKERS, TASK_SHUTDOWN_TIMEOUT
from database.models import create_task, update_task_status, get_task
from utils.logger import get_logger, get_task_logger

logger = get_logger(__name__)


class TaskManager:
    def __init__(self):
        self._executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
            thread_name_prefix="scraper-worker",
        )
        self._lock = threading.Lock()
        self._cancelled: set[str] = set()  # task_ids that have been cancelled
        logger.info(f"TaskManager initialized with {MAX_WORKERS} workers.")

    def submit_task(
        self,
        source: str,
        worker_fn: Callable,
        keyword: str = "",
        location: str = "",
        dork_query: str = "",
        max_results: int = 20,
    ) -> str:

        task_id = str(uuid.uuid4())

        create_task(
            task_id=task_id,
            source=source,
            keyword=keyword,
            location=location,
            dork_query=dork_query,
            max_results=max_results,
        )

        task_logger = get_task_logger(task_id)
        task_logger.info(
            f"Task created | source={source} | keyword='{keyword}' "
            f"| location='{location}' | dork='{dork_query}' | max={max_results}"
        )

        self._executor.submit(
            self._run_task,
            task_id=task_id,
            worker_fn=worker_fn,
            keyword=keyword,
            location=location,
            dork_query=dork_query,
            max_results=max_results,
        )

        logger.info(f"Task {task_id} submitted.")
        return task_id

    def cancel_task(self, task_id: str) -> bool:

        task = get_task(task_id)
        if not task:
            return False
        if task["status"] in ("completed", "failed", "cancelled"):
            return False

        with self._lock:
            self._cancelled.add(task_id)

        update_task_status(
            task_id,
            status="cancelled",
            progress=task.get("progress", 0),
            total=task.get("total", 0),
        )
        logger.info(f"Task {task_id} marked for cancellation.")
        return True

    def is_task_cancelled(self, task_id: str) -> bool:

        with self._lock:
            return task_id in self._cancelled

    def get_task_logs(self, task_id: str, tail: int = 50) -> list[str]:
        from core.config import LOGS_DIR

        log_file = LOGS_DIR / f"{task_id}.log"
        if not log_file.exists():
            return []
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
        return [line.rstrip() for line in lines[-tail:]]

    def shutdown(self) -> None:

        logger.info(
            f"TaskManager shutting down — waiting up to {TASK_SHUTDOWN_TIMEOUT}s "
            "for running tasks…"
        )
        self._executor.shutdown(wait=True, cancel_futures=False)
        logger.info("TaskManager shutdown complete.")

    def _run_task(
        self,
        task_id: str,
        worker_fn: Callable,
        **kwargs,
    ) -> None:

        task_logger = get_task_logger(task_id)

        if self.is_task_cancelled(task_id):
            task_logger.info("Task was cancelled before it started.")
            return

        update_task_status(task_id, status="running", progress=0)
        task_logger.info("Task worker started.")

        try:
            worker_fn(
                task_id=task_id,
                task_logger=task_logger,
                task_manager=self,
                **kwargs,
            )

            task = get_task(task_id)
            if task and task["status"] not in ("cancelled", "failed"):
                update_task_status(
                    task_id,
                    status="completed",
                    progress=task.get("total", 0),
                    total=task.get("total", 0),
                )
                task_logger.info("Task completed successfully.")

        except Exception as exc:
            logger.exception(f"Task {task_id} worker raised: {exc}")
            update_task_status(task_id, status="failed", error=str(exc))
            task_logger.error(f"Task failed: {exc}")

        finally:
            # Always clean up the cancelled set
            with self._lock:
                self._cancelled.discard(task_id)
