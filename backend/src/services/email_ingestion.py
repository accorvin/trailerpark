"""Local directory scanner for OneDrive-synced emails from Power Automate."""

import json
import logging
import mimetypes
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from pydantic import ValidationError

from ..config import get_settings
from ..models import Attachment, Email
from ..schemas import BuyerRequestBase, ListingBase
from .attachment_extractor import extract_text
from .llm_parser import classify_email, extract_buyer_requests, extract_listings

logger = logging.getLogger(__name__)
settings = get_settings()


def scan_emails(db: Session) -> int:
    """Scan EMAIL_DIR for new email folders and process them.

    Returns the number of new emails processed.
    """
    email_dir = settings.email_dir_path
    if not email_dir.exists():
        logger.warning("EMAIL_DIR does not exist: %s", email_dir)
        return 0

    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    prev_month_dt = now.replace(day=1) - __import__("datetime").timedelta(days=1)
    prev_month = prev_month_dt.strftime("%Y-%m")

    months_to_scan = [prev_month, current_month]
    processed = 0

    for month in months_to_scan:
        month_dir = email_dir / month
        if not month_dir.exists():
            continue

        for email_folder in sorted(month_dir.iterdir()):
            if not email_folder.is_dir() or email_folder.is_symlink():
                continue

            email_id = f"{month}/{email_folder.name}"

            existing = db.get(Email, email_id)
            if existing:
                continue

            try:
                processed += _process_email_folder(db, email_id, email_folder)
            except Exception:
                logger.exception("Error processing email folder: %s", email_id)
                db.rollback()
                _store_error_email(db, email_id, email_folder)

    logger.info("Processed %d new emails", processed)
    return processed


def _process_email_folder(db: Session, email_id: str, folder: Path) -> int:
    """Process a single email folder. Returns 1 on success, 0 on skip."""
    metadata_path = folder / "metadata.json"
    if not metadata_path.exists():
        logger.warning("No metadata.json in %s, skipping", folder)
        return 0

    raw_json = metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(raw_json)

    received_at = None
    if metadata.get("received_at"):
        try:
            received_at = datetime.fromisoformat(metadata["received_at"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    email = Email(
        id=email_id,
        from_address=metadata.get("from_address"),
        from_name=metadata.get("from_name"),
        subject=metadata.get("subject"),
        body_text=metadata.get("body_text"),
        body_html=metadata.get("body_html"),
        received_at=received_at,
        raw_json=raw_json,
    )
    db.add(email)

    # Inventory and copy attachments
    attachment_texts = []
    att_root = settings.attachment_dir_path.resolve()
    for file_path in sorted(folder.iterdir()):
        if file_path.name == "metadata.json" or not file_path.is_file():
            continue
        if file_path.is_symlink():
            logger.warning("Skipping symlink: %s", file_path)
            continue

        content_type, _ = mimetypes.guess_type(str(file_path))
        file_size = file_path.stat().st_size

        # Skip small inline images (likely signature icons)
        is_image = content_type and content_type.startswith("image/")
        if is_image and file_size < 10240:
            continue

        # Copy attachment to app's storage (with path containment check)
        dest_dir = (settings.attachment_dir_path / email_id).resolve()
        if not str(dest_dir).startswith(str(att_root)):
            logger.warning("Path traversal blocked for email_id: %s", email_id)
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_path.name
        if not str(dest_path.resolve()).startswith(str(att_root)):
            logger.warning("Path traversal blocked for filename: %s", file_path.name)
            continue
        shutil.copy2(file_path, dest_path)

        relative_path = f"{email_id}/{file_path.name}"

        # Extract text from PDFs/Excel
        extracted_text = extract_text(file_path, content_type)
        if extracted_text:
            attachment_texts.append(extracted_text)

        attachment = Attachment(
            email_id=email_id,
            filename=file_path.name,
            file_path=relative_path,
            content_type=content_type,
            file_size=file_size,
            extracted_text=extracted_text,
            is_inline=False,
        )
        db.add(attachment)

    # Classify email
    full_text = _build_full_text(email, attachment_texts)
    classification = classify_email(email.subject or "", full_text)
    email.classification = classification

    # Extract structured data based on classification (with Pydantic validation)
    if classification == "seller_listing":
        listings = extract_listings(email.subject or "", full_text)
        for listing_data in listings:
            try:
                ListingBase.model_validate(listing_data)
            except ValidationError:
                logger.warning("Skipping invalid listing from %s: %s", email_id, listing_data)
                continue
            listing_data["email_id"] = email_id
            from ..models import Listing

            listing = Listing(**listing_data)
            db.add(listing)

    elif classification == "buyer_request":
        requests = extract_buyer_requests(email.subject or "", full_text)
        for req_data in requests:
            try:
                BuyerRequestBase.model_validate(req_data)
            except ValidationError:
                logger.warning("Skipping invalid buyer request from %s: %s", email_id, req_data)
                continue
            req_data["email_id"] = email_id
            from ..models import BuyerRequest

            buyer_req = BuyerRequest(**req_data)
            db.add(buyer_req)

    db.commit()
    logger.info("Processed email: %s (classification: %s)", email_id, classification)
    return 1


def _build_full_text(email: Email, attachment_texts: list[str]) -> str:
    """Build the full text from email body and attachment extracted texts."""
    parts = []
    if email.body_text:
        parts.append(email.body_text)
    for text in attachment_texts:
        parts.append(text)
    return "\n\n---\n\n".join(parts)


def _store_error_email(db: Session, email_id: str, folder: Path):
    """Store an email record with parse_error classification."""
    try:
        raw_json = None
        metadata_path = folder / "metadata.json"
        if metadata_path.exists():
            raw_json = metadata_path.read_text(encoding="utf-8")

        email = Email(
            id=email_id,
            classification="parse_error",
            raw_json=raw_json,
        )
        db.add(email)
        db.commit()
    except Exception:
        logger.exception("Failed to store error email: %s", email_id)
        db.rollback()
