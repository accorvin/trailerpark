"""Gmail-based email ingestion service."""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from pydantic import ValidationError

from ..config import get_settings
from ..models import Attachment, Email, GmailSyncState
from ..schemas import BuyerRequestBase, ListingBase
from .attachment_extractor import extract_text
from .gmail_client import (
    download_attachments,
    fetch_new_messages,
    get_gmail_service,
    get_history,
    get_message,
    is_gmail_configured,
    parse_message,
)
from .llm_parser import classify_email, extract_buyer_requests, extract_listings

logger = logging.getLogger(__name__)
settings = get_settings()

_scan_lock = threading.Lock()


def scan_emails(db: Session) -> int:
    """Fetch new emails from Gmail and process them.

    Returns the number of new emails processed.
    """
    if not is_gmail_configured():
        logger.info("Gmail not configured — skipping scan")
        return 0

    if not _scan_lock.acquire(blocking=False):
        logger.info("Email scan already in progress — skipping")
        return 0

    try:
        return _do_scan(db)
    finally:
        _scan_lock.release()


def _do_scan(db: Session) -> int:
    service = get_gmail_service()
    sync_state = db.query(GmailSyncState).first()
    query = settings.GMAIL_QUERY

    message_ids: list[str] = []

    # Try incremental sync via historyId first
    if sync_state and sync_state.last_history_id:
        new_ids, latest_history_id = get_history(service, sync_state.last_history_id)
        if latest_history_id is not None:
            # History is valid — use incremental results
            message_ids = new_ids
            if latest_history_id:
                _update_sync_state(db, sync_state, latest_history_id)
            return _process_message_ids(db, service, message_ids)

    # Fall back to full query (first run or history expired)
    after_epoch = None
    if sync_state and sync_state.last_sync_at:
        after_epoch = int(sync_state.last_sync_at.timestamp())
    else:
        # First sync — limit scope
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.GMAIL_INITIAL_SYNC_DAYS)
        after_epoch = int(cutoff.timestamp())

    messages = fetch_new_messages(service, query, after_epoch=after_epoch)
    processed = _process_messages(db, service, messages)

    # Store the latest historyId from the most recently fetched message
    if messages:
        latest_hid = max(msg.get("historyId", "0") for msg in messages)
        _update_sync_state(db, sync_state, latest_hid)

    return processed


def _process_message_ids(db: Session, service, message_ids: list[str]) -> int:
    """Fetch and process messages by ID, skipping already-processed ones."""
    processed = 0
    for msg_id in message_ids:
        if db.get(Email, msg_id):
            continue
        try:
            msg = get_message(service, msg_id)
            processed += _process_gmail_message(db, service, msg)
        except Exception:
            logger.exception("Error processing Gmail message: %s", msg_id)
            db.rollback()
            _store_error_email(db, msg_id)
    return processed


def _process_messages(db: Session, service, messages: list[dict]) -> int:
    """Process a list of full message resources."""
    processed = 0
    for msg in messages:
        msg_id = msg["id"]
        if db.get(Email, msg_id):
            continue
        try:
            processed += _process_gmail_message(db, service, msg)
        except Exception:
            logger.exception("Error processing Gmail message: %s", msg_id)
            db.rollback()
            _store_error_email(db, msg_id)
    return processed


def _process_gmail_message(db: Session, service, msg: dict) -> int:
    """Process a single Gmail message. Returns 1 on success, 0 on skip."""
    parsed = parse_message(msg)

    email = Email(
        id=parsed["id"],
        from_address=parsed["from_address"],
        from_name=parsed["from_name"],
        subject=parsed["subject"],
        body_text=parsed["body_text"],
        body_html=parsed["body_html"],
        received_at=parsed["received_at"],
        raw_json=parsed["raw_json"],
    )
    db.add(email)

    # Download and process attachments
    att_root = settings.attachment_dir_path.resolve()
    dest_dir = (settings.attachment_dir_path / parsed["id"]).resolve()
    if not str(dest_dir).startswith(str(att_root)):
        logger.warning("Path traversal blocked for email_id: %s", parsed["id"])
        db.commit()
        return 1

    attachment_texts = []
    downloaded = download_attachments(service, msg, dest_dir)

    for att_info in downloaded:
        file_path = att_info["file_path"]
        extracted_text = extract_text(file_path, att_info["content_type"])
        if extracted_text:
            attachment_texts.append(extracted_text)

        relative_path = f"{parsed['id']}/{att_info['filename']}"
        attachment = Attachment(
            email_id=parsed["id"],
            filename=att_info["filename"],
            file_path=relative_path,
            content_type=att_info["content_type"],
            file_size=att_info["file_size"],
            extracted_text=extracted_text,
            is_inline=False,
        )
        db.add(attachment)

    # Classify email
    full_text = _build_full_text(email, attachment_texts)
    classification = classify_email(email.subject or "", full_text)
    email.classification = classification

    # Extract structured data based on classification
    if classification == "seller_listing":
        listings = extract_listings(email.subject or "", full_text)
        for listing_data in listings:
            try:
                ListingBase.model_validate(listing_data)
            except ValidationError:
                logger.warning("Skipping invalid listing from %s: %s", parsed["id"], listing_data)
                continue
            listing_data["email_id"] = parsed["id"]
            from ..models import Listing
            listing = Listing(**listing_data)
            db.add(listing)

    elif classification == "buyer_request":
        requests = extract_buyer_requests(email.subject or "", full_text)
        for req_data in requests:
            try:
                BuyerRequestBase.model_validate(req_data)
            except ValidationError:
                logger.warning("Skipping invalid buyer request from %s: %s", parsed["id"], req_data)
                continue
            req_data["email_id"] = parsed["id"]
            from ..models import BuyerRequest
            buyer_req = BuyerRequest(**req_data)
            db.add(buyer_req)

    db.commit()
    logger.info("Processed email: %s (classification: %s)", parsed["id"], classification)
    return 1


def _build_full_text(email: Email, attachment_texts: list[str]) -> str:
    """Build the full text from email body and attachment extracted texts."""
    parts = []
    if email.body_text:
        parts.append(email.body_text)
    for text in attachment_texts:
        parts.append(text)
    return "\n\n---\n\n".join(parts)


def _update_sync_state(db: Session, sync_state: GmailSyncState | None, history_id: str):
    """Create or update the Gmail sync state."""
    now = datetime.now(timezone.utc)
    if sync_state:
        sync_state.last_history_id = history_id
        sync_state.last_sync_at = now
        sync_state.last_sync_status = "ok"
        sync_state.last_sync_error = None
    else:
        sync_state = GmailSyncState(
            last_history_id=history_id,
            last_sync_at=now,
            last_sync_status="ok",
        )
        db.add(sync_state)
    db.commit()


def _store_error_email(db: Session, msg_id: str):
    """Store an email record with parse_error classification."""
    try:
        email = Email(id=msg_id, classification="parse_error")
        db.add(email)
        db.commit()
    except Exception:
        logger.exception("Failed to store error email: %s", msg_id)
        db.rollback()
