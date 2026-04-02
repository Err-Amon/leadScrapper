import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database.db import init_db
from api.routes import router, task_manager
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing database…")
    init_db()
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down — draining task workers…")
    task_manager.shutdown()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Lead Generation Tool API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)


@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle CORS preflight requests explicitly."""
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get(
                "origin", "http://localhost:3000"
            ),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600",
        },
    )


app.include_router(router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
