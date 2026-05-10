import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings

settings = get_settings()


def setup_logging():
    log_dir = settings.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_dir / "trailerpark.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root_logger.addHandler(console_handler)


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .tasks.scheduler import start_scheduler, shutdown_scheduler

    logger.info("Starting TrailerPark application")
    start_scheduler()
    yield
    logger.info("Shutting down TrailerPark application")
    shutdown_scheduler()


app = FastAPI(title="TrailerPark", version="0.1.0", lifespan=lifespan)

# Look for frontend dist in multiple locations (local dev vs Docker)
_src_dir = Path(__file__).resolve().parent
frontend_dist = _src_dir.parent.parent / "frontend" / "dist"  # local: backend/../frontend/dist
if not frontend_dist.exists():
    frontend_dist = _src_dir.parent / "frontend" / "dist"  # Docker: /app/frontend/dist

# CORS only in development (when frontend dist doesn't exist, Vite dev server is on a different port)
if not frontend_dist.exists():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Import and register routers
from .routers import listings, buyers, deals, matches, benchmarks, emails, stats, attachments, auth  # noqa: E402

app.include_router(listings.router, prefix="/api")
app.include_router(buyers.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(benchmarks.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# Serve frontend static files in production
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
