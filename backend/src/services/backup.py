"""Database backup and attachment cleanup."""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Listing

logger = logging.getLogger(__name__)
settings = get_settings()


def backup_database() -> Path | None:
    """Create a daily backup of the SQLite database using VACUUM INTO.

    Returns the backup file path, or None on failure.
    """
    import sqlite3

    backup_dir = settings.backup_dir_path
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = settings.database_path
    if not db_path.exists():
        logger.warning("Database file not found: %s", db_path)
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    backup_path = backup_dir / f"trailerpark-{today}.db"

    try:
        # Remove existing backup for today if it exists (re-run)
        if backup_path.exists():
            backup_path.unlink()

        conn = sqlite3.connect(str(db_path))
        # Use parameterized query to avoid SQL injection via path
        conn.execute("VACUUM INTO ?", (str(backup_path),))
        conn.close()

        logger.info("Database backed up to %s", backup_path)

        # Clean up old backups (keep 7 days)
        _cleanup_old_backups(backup_dir, keep_days=7)

        return backup_path

    except Exception:
        logger.exception("Database backup failed")
        return None


def _cleanup_old_backups(backup_dir: Path, keep_days: int = 7):
    """Delete backup files older than keep_days."""
    cutoff = datetime.now() - timedelta(days=keep_days)

    for f in backup_dir.iterdir():
        if not f.name.startswith("trailerpark-") or not f.name.endswith(".db"):
            continue
        try:
            # Parse date from filename
            date_str = f.name[len("trailerpark-"):-len(".db")]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                f.unlink()
                logger.info("Deleted old backup: %s", f.name)
        except (ValueError, OSError):
            pass


def cleanup_old_attachments(db: Session) -> int:
    """Delete attachment files for archived listings older than ATTACHMENT_MAX_AGE_DAYS.

    Returns count of files deleted.
    """
    cutoff = datetime.now() - timedelta(days=settings.ATTACHMENT_MAX_AGE_DAYS)

    old_listings = (
        db.query(Listing)
        .filter(
            Listing.is_archived == True,
            Listing.archived_at < cutoff,
        )
        .all()
    )

    deleted = 0
    att_dir = settings.attachment_dir_path

    for listing in old_listings:
        email_id = listing.email_id
        listing_att_dir = att_dir / email_id
        if listing_att_dir.exists():
            for f in listing_att_dir.iterdir():
                if f.is_file():
                    f.unlink()
                    deleted += 1
            # Remove empty directory
            try:
                listing_att_dir.rmdir()
            except OSError:
                pass

    if deleted > 0:
        logger.info("Cleaned up %d old attachment files", deleted)

    return deleted
