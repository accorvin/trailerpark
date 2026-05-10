"""APScheduler setup for background jobs."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from ..config import get_settings
from ..database import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = BackgroundScheduler()


def _run_email_scan():
    """Scan for new emails."""
    from ..services.email_ingestion import scan_emails

    db = SessionLocal()
    try:
        scan_emails(db)
    except Exception:
        logger.exception("Email scan job failed")
    finally:
        db.close()


def _run_archive():
    """Archive old listings and buyer requests."""
    from ..services.archiver import archive_old

    db = SessionLocal()
    try:
        archive_old(db)
    except Exception:
        logger.exception("Archive job failed")
    finally:
        db.close()


def _run_deal_detection():
    """Re-run deal detection for all active listings."""
    from ..services.deal_detector import detect_deals_all

    db = SessionLocal()
    try:
        detect_deals_all(db)
    except Exception:
        logger.exception("Deal detection job failed")
    finally:
        db.close()


def _run_matching():
    """Re-run buyer-seller matching."""
    from ..services.matcher import match_all

    db = SessionLocal()
    try:
        match_all(db)
    except Exception:
        logger.exception("Matching job failed")
    finally:
        db.close()


def _run_backup():
    """Back up the database."""
    from ..services.backup import backup_database

    try:
        backup_database()
    except Exception:
        logger.exception("Backup job failed")


def _run_attachment_cleanup():
    """Clean up old attachment files."""
    from ..services.backup import cleanup_old_attachments

    db = SessionLocal()
    try:
        cleanup_old_attachments(db)
    except Exception:
        logger.exception("Attachment cleanup job failed")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler with all jobs."""
    scheduler.add_job(
        _run_email_scan,
        "interval",
        minutes=settings.SCAN_INTERVAL_MINUTES,
        id="scan_emails",
        name="Scan for new emails",
    )

    scheduler.add_job(
        _run_archive,
        "cron",
        hour=2, minute=0,
        id="archive_old",
        name="Archive old listings",
    )

    scheduler.add_job(
        _run_deal_detection,
        "cron",
        hour=3, minute=0,
        id="detect_deals",
        name="Re-run deal detection",
    )

    scheduler.add_job(
        _run_matching,
        "cron",
        hour=3, minute=30,
        id="match_all",
        name="Re-run matching",
    )

    scheduler.add_job(
        _run_backup,
        "cron",
        hour=1, minute=0,
        id="backup_db",
        name="Daily DB backup",
    )

    scheduler.add_job(
        _run_attachment_cleanup,
        "cron",
        hour=4, minute=0,
        id="cleanup_attachments",
        name="Clean up old attachments",
    )

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    # Run initial scan on startup
    logger.info("Running initial email scan...")
    _run_email_scan()


def shutdown_scheduler():
    """Shut down the scheduler gracefully."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")
