import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

from core.config import MAX_WORKERS
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

        logger.info(f"Task {task_id} submitted to worker pool.")
        return task_id

    def _run_task(
        self,
        task_id: str,
        worker_fn: Callable,
        **kwargs,
    ) -> None:

        task_logger = get_task_logger(task_id)
        update_task_status(task_id, status="running", progress=0)
        task_logger.info("Task started.")

        try:
            worker_fn(task_id=task_id, task_logger=task_logger, **kwargs)
            task = get_task(task_id)
            update_task_status(
                task_id,
                status="completed",
                progress=task.get("total", 0),
                total=task.get("total", 0),
            )
            task_logger.info("Task completed successfully.")

        except Exception as exc:
            logger.exception(f"Task {task_id} raised an unhandled exception: {exc}")
            update_task_status(
                task_id,
                status="failed",
                error=str(exc),
            )
            task_logger.error(f"Task failed: {exc}")

    def get_task_logs(self, task_id: str, tail: int = 50) -> list[str]:

        from core.config import LOGS_DIR

        log_file = LOGS_DIR / f"{task_id}.log"
        if not log_file.exists():
            return []
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
        return [line.rstrip() for line in lines[-tail:]]

    def shutdown(self) -> None:
        logger.info("Shutting down TaskManager...")
        self._executor.shutdown(wait=True)
        logger.info("TaskManager shutdown complete.")
