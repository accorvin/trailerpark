from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, event

import sys

# Add backend directory to path so we can import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import Base
from src.models import Email, Listing, BuyerRequest, PriceBenchmark, Attachment, Match  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Resolve relative DB path from project root
    url = config.get_main_option("sqlalchemy.url")
    if url and url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel = url[len("sqlite:///"):]
        abs_path = (Path(__file__).resolve().parent.parent / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{abs_path}"

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
