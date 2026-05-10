import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

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


# Auth paths that must be accessible without a session
PUBLIC_PATH_PREFIXES = (
    "/api/auth/login",
    "/api/auth/callback",
    "/api/auth/status",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Require a valid session cookie for all /api/* routes (except auth endpoints)."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public paths and non-API routes (static files handled by mount)
        if not path.startswith("/api/") or path.startswith(PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        # Check session
        from .routers.auth import verify_session, SESSION_COOKIE, set_session_cookie
        email = verify_session(request)
        if not email:
            # API calls get 401, browser navigations would be handled by the frontend
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        # Sliding session: refresh cookie on each authenticated request
        response = await call_next(request)
        set_session_cookie(response, email)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .tasks.scheduler import start_scheduler, shutdown_scheduler

    logger.info("Starting TrailerPark application")
    start_scheduler()
    yield
    logger.info("Shutting down TrailerPark application")
    shutdown_scheduler()


app = FastAPI(title="TrailerPark", version="0.1.0", lifespan=lifespan)

# Auth middleware
app.add_middleware(AuthMiddleware)

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

@app.get("/api/health")
def health():
    return {"status": "ok"}


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
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all non-API routes so the SPA router handles them."""
        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
