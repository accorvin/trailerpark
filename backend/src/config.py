import os
from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# On Railway, data lives on a persistent volume at /app/data.
# Locally, data lives at backend/data/.
_RAILWAY = os.environ.get("RAILWAY_ENVIRONMENT")
DATA_DIR = Path("/app/data") if _RAILWAY else (PROJECT_ROOT / "data").resolve()


class Settings(BaseSettings):
    model_config = {"env_file": PROJECT_ROOT / ".env", "env_file_encoding": "utf-8"}

    OPENAI_API_KEY: str
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'trailerpark.db'}"
    SCAN_INTERVAL_MINUTES: int = 5
    ARCHIVE_DAYS: int = 20
    DEAL_THRESHOLD: int = 10000
    ATTACHMENT_MAX_AGE_DAYS: int = 90
    PORT: int = 8000
    OPENAI_MAX_CONCURRENT: int = 5

    # Gmail OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GMAIL_QUERY: str = "label:inbox"
    GMAIL_INITIAL_SYNC_DAYS: int = 30

    # Base URL for OAuth callbacks (set automatically on Railway)
    BASE_URL: str | None = None

    @property
    def data_dir_path(self) -> Path:
        return DATA_DIR

    @property
    def database_path(self) -> Path:
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            return Path(url[len("sqlite:///"):])
        return Path(url)

    @property
    def database_url_resolved(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def attachment_dir_path(self) -> Path:
        return DATA_DIR / "attachments"

    @property
    def log_dir_path(self) -> Path:
        return DATA_DIR / "logs"

    @property
    def backup_dir_path(self) -> Path:
        return DATA_DIR / "backups"

    @property
    def base_url(self) -> str:
        if self.BASE_URL:
            return self.BASE_URL.rstrip("/")
        # Auto-detect on Railway
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        if domain:
            return f"https://{domain}"
        return f"http://localhost:{self.PORT}"


def get_settings() -> Settings:
    return Settings()
