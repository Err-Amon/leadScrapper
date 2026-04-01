from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from core.task_manager import TaskManager
from database.models import (
    get_task,
    get_all_tasks,
    get_leads_by_task,
    get_task_lead_count,
)
from exporter.csv_exporter import generate_csv
from scraper.maps_scraper import run_maps_scrape
from scraper.dorks_scraper import run_dorks_scrape
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
task_manager = TaskManager()


class StartMapsTaskRequest(BaseModel):
    keyword: str = Field(
        ..., min_length=1, description="Search keyword, e.g. 'plumbers'"
    )
    location: str = Field(
        ..., min_length=1, description="Location, e.g. 'Lahore, Pakistan'"
    )
    max_results: int = Field(default=20, ge=1, le=100)


class StartDorksTaskRequest(BaseModel):
    dork_query: str = Field(..., min_length=1, description="Google dork query string")
    max_results: int = Field(default=20, ge=1, le=100)


class TaskResponse(BaseModel):
    id: str
    status: str
    source: str
    keyword: Optional[str] = None
    location: Optional[str] = None
    dork_query: Optional[str] = None
    max_results: int
    progress: int
    total: int
    error: Optional[str] = None
    created_at: str
    updated_at: str


class LeadsResponse(BaseModel):
    task_id: str
    page: int
    page_size: int
    total: int
    total_pages: int
    leads: list[dict]


@router.post("/tasks/maps", status_code=202)
def start_maps_task(body: StartMapsTaskRequest):

    task_id = task_manager.submit_task(
        source="maps",
        worker_fn=run_maps_scrape,
        keyword=body.keyword,
        location=body.location,
        max_results=body.max_results,
    )
    logger.info(f"Maps task accepted: {task_id}")
    return {"task_id": task_id, "status": "pending"}


@router.post("/tasks/dorks", status_code=202)
def start_dorks_task(body: StartDorksTaskRequest):

    task_id = task_manager.submit_task(
        source="dorks",
        worker_fn=run_dorks_scrape,
        dork_query=body.dork_query,
        max_results=body.max_results,
    )
    logger.info(f"Dorks task accepted: {task_id}")
    return {"task_id": task_id, "status": "pending"}


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks():
    """Return the 50 most recently created tasks."""
    return get_all_tasks(limit=50)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@router.get("/tasks/{task_id}/logs")
def get_task_logs(
    task_id: str,
    tail: int = Query(default=50, ge=1, le=200),
):
    """Return the last N log lines from the task's log file."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    lines = task_manager.get_task_logs(task_id, tail=tail)
    return {"task_id": task_id, "logs": lines}


@router.get("/tasks/{task_id}/results", response_model=LeadsResponse)
def get_results(
    task_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default="", description="Free-text search across all fields"),
    source: str = Query(default="", description="Filter by source: 'maps' or 'dorks'"),
    has_email: bool = Query(
        default=False, description="Only return leads with an email"
    ),
    has_phone: bool = Query(
        default=False, description="Only return leads with a phone"
    ),
):

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    leads, total = get_leads_by_task(
        task_id=task_id,
        page=page,
        page_size=page_size,
        search=search,
        source_filter=source,
        has_email=has_email,
        has_phone=has_phone,
    )

    total_pages = max(1, -(-total // page_size))  # Ceiling division

    return {
        "task_id": task_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "leads": leads,
    }


@router.get("/tasks/{task_id}/export")
def export_csv(
    task_id: str,
    search: str = Query(default=""),
    source: str = Query(default=""),
    has_email: bool = Query(default=False),
    has_phone: bool = Query(default=False),
):

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task["status"] not in ("completed", "running"):
        raise HTTPException(
            status_code=400,
            detail="Task must be running or completed before exporting.",
        )

    lead_count = get_task_lead_count(task_id)
    if lead_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No leads collected yet for this task.",
        )

    try:
        csv_path = generate_csv(
            task_id=task_id,
            search=search,
            source_filter=source,
            has_email=has_email,
            has_phone=has_phone,
        )
    except Exception as exc:
        logger.error(f"CSV export failed for task {task_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=csv_path.name,
        headers={"Content-Disposition": f'attachment; filename="{csv_path.name}"'},
    )


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "lead-gen-tool", "phase": 3}
