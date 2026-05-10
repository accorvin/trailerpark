from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = {"env_file": PROJECT_ROOT / ".env", "env_file_encoding": "utf-8"}

    OPENAI_API_KEY: str
    DATABASE_URL: str = "sqlite:///data/trailerpark.db"
    SCAN_INTERVAL_MINUTES: int = 5
    ARCHIVE_DAYS: int = 20
    DEAL_THRESHOLD: int = 10000
    ATTACHMENT_DIR: str = "data/attachments"
    ATTACHMENT_MAX_AGE_DAYS: int = 90
    LOG_DIR: str = "data/logs"
    PORT: int = 8000
    BACKUP_DIR: str = "data/backups"
    OPENAI_MAX_CONCURRENT: int = 5

    # Gmail OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GMAIL_QUERY: str = "label:inbox"
    GMAIL_INITIAL_SYNC_DAYS: int = 30

    @property
    def data_dir_path(self) -> Path:
        return (PROJECT_ROOT / "data").resolve()

    @property
    def database_path(self) -> Path:
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            rel = url[len("sqlite:///"):]
            return (PROJECT_ROOT / rel).resolve()
        return Path(url)

    @property
    def database_url_resolved(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def attachment_dir_path(self) -> Path:
        return (PROJECT_ROOT / self.ATTACHMENT_DIR).resolve()

    @property
    def log_dir_path(self) -> Path:
        return (PROJECT_ROOT / self.LOG_DIR).resolve()

    @property
    def backup_dir_path(self) -> Path:
        return (PROJECT_ROOT / self.BACKUP_DIR).resolve()


def get_settings() -> Settings:
    return Settings()
