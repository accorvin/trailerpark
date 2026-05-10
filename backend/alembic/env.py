from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, event

import sys

# Add backend directory to path so we can import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_settings
from src.database import Base
from src.models import Email, Listing, BuyerRequest, PriceBenchmark, Attachment, Match, GmailSyncState  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def run_migrations_offline():
    url = settings.database_url_resolved
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = settings.database_url_resolved
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connectable = create_engine(url)
    event.listen(connectable, "connect", _set_sqlite_pragmas)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
