import logging
from database.models import update_task_status
from utils.logger import get_logger

logger = get_logger(__name__)


def run_dorks_scrape(
    task_id: str,
    task_logger: logging.Logger,
    dork_query: str = "",
    max_results: int = 20,
    **kwargs,
) -> None:

    task_logger.info(f"Dorks scraper started | query='{dork_query}'")
    update_task_status(task_id, status="running", progress=0, total=max_results)

    # Phase 4 will implement the actual dork search and page-visiting loop.
    task_logger.info("Dorks scraper: Phase 4 implementation pending.")
    update_task_status(task_id, status="completed", progress=0, total=0)
