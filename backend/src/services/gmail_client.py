"""Gmail API client for fetching emails."""

import base64
import json
import logging
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TOKEN_PATH = settings.data_dir_path / "gmail_token.json"


def is_gmail_configured() -> bool:
    """Check if Gmail OAuth credentials exist and are usable."""
    if not TOKEN_PATH.exists():
        return False
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return False
    return True


def get_credentials() -> Credentials | None:
    """Load and refresh Gmail OAuth credentials from disk."""
    if not TOKEN_PATH.exists():
        return None

    creds = Credentials.from_authorized_user_file(
        str(TOKEN_PATH),
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        except Exception:
            logger.exception("Failed to refresh Gmail token — re-authentication required")
            return None

    return creds


def get_gmail_service():
    """Return an authenticated Gmail API service object."""
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Gmail not authenticated. Run: uv run python -m src.setup_gmail")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_new_messages(
    service, query: str, after_epoch: int | None = None, max_results: int = 100
) -> list[dict]:
    """Fetch messages matching a query, optionally after a timestamp.

    Returns a list of full message resources.
    """
    q = query
    if after_epoch:
        q = f"{q} after:{after_epoch}"

    messages = []
    page_token = None

    while True:
        result = _call_with_backoff(
            service.users().messages().list,
            userId="me",
            q=q,
            maxResults=min(max_results - len(messages), 100),
            pageToken=page_token,
        )

        batch = result.get("messages", [])
        if not batch:
            break

        for msg_stub in batch:
            msg = _call_with_backoff(
                service.users().messages().get,
                userId="me",
                id=msg_stub["id"],
                format="full",
            )
            messages.append(msg)

            if len(messages) >= max_results:
                return messages

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return messages


def get_history(service, start_history_id: str) -> tuple[list[str], str | None]:
    """Get message IDs added since a history ID.

    Returns (list of new message IDs, latest history ID or None if history expired).
    """
    new_ids = []
    page_token = None

    try:
        while True:
            result = _call_with_backoff(
                service.users().history().list,
                userId="me",
                startHistoryId=start_history_id,
                historyTypes=["messageAdded"],
                pageToken=page_token,
            )

            for record in result.get("history", []):
                for added in record.get("messagesAdded", []):
                    new_ids.append(added["message"]["id"])

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return new_ids, result.get("historyId")

    except HttpError as e:
        if e.resp.status == 404:
            logger.warning("Gmail history expired, falling back to full sync")
            return [], None
        raise


def get_message(service, message_id: str) -> dict:
    """Fetch a single full message by ID."""
    return _call_with_backoff(
        service.users().messages().get,
        userId="me",
        id=message_id,
        format="full",
    )


def parse_message(msg: dict) -> dict:
    """Parse a Gmail API message into a flat dict with sender, subject, body, etc."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

    from_raw = headers.get("from", "")
    from_name, from_address = _parse_from(from_raw)

    received_at = None
    internal_ts = msg.get("internalDate")
    if internal_ts:
        from datetime import datetime, timezone
        received_at = datetime.fromtimestamp(int(internal_ts) / 1000, tz=timezone.utc)

    body_text, body_html = _extract_body(msg["payload"])

    return {
        "id": msg["id"],
        "from_name": from_name,
        "from_address": from_address,
        "subject": headers.get("subject"),
        "body_text": body_text,
        "body_html": body_html,
        "received_at": received_at,
        "history_id": msg.get("historyId"),
        "raw_json": json.dumps(msg),
    }


def download_attachments(service, msg: dict, dest_dir: Path) -> list[dict]:
    """Download all attachments from a message to dest_dir.

    Returns a list of dicts with filename, content_type, file_size, file_path.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    attachments = []

    def _walk_parts(parts):
        for part in parts:
            filename = part.get("filename")
            if filename and part.get("body", {}).get("size", 0) > 0:
                # Skip small inline images (likely signature icons)
                content_type = part.get("mimeType", "application/octet-stream")
                is_image = content_type.startswith("image/")
                size = part["body"].get("size", 0)
                if is_image and size < 10240:
                    continue

                attachment_id = part["body"].get("attachmentId")
                if attachment_id:
                    att_data = _call_with_backoff(
                        service.users().messages().attachments().get,
                        userId="me",
                        messageId=msg["id"],
                        id=attachment_id,
                    )
                    data = base64.urlsafe_b64decode(att_data["data"])
                else:
                    data = base64.urlsafe_b64decode(part["body"]["data"])

                file_path = dest_dir / filename
                file_path.write_bytes(data)

                attachments.append({
                    "filename": filename,
                    "content_type": content_type,
                    "file_size": len(data),
                    "file_path": file_path,
                })

            if "parts" in part:
                _walk_parts(part["parts"])

    payload = msg.get("payload", {})
    if "parts" in payload:
        _walk_parts(payload["parts"])

    return attachments


def _extract_body(payload: dict) -> tuple[str | None, str | None]:
    """Recursively walk MIME parts to extract text/plain and text/html bodies."""
    text_body = None
    html_body = None

    def _walk(part):
        nonlocal text_body, html_body
        mime = part.get("mimeType", "")

        if mime == "text/plain" and not text_body:
            data = part.get("body", {}).get("data")
            if data:
                text_body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        elif mime == "text/html" and not html_body:
            data = part.get("body", {}).get("data")
            if data:
                html_body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        for sub in part.get("parts", []):
            _walk(sub)

    _walk(payload)
    return text_body, html_body


def _parse_from(from_header: str) -> tuple[str | None, str | None]:
    """Parse 'Display Name <email@example.com>' into (name, address)."""
    if "<" in from_header and ">" in from_header:
        name = from_header[:from_header.index("<")].strip().strip('"')
        address = from_header[from_header.index("<") + 1:from_header.index(">")].strip()
        return (name or None, address)
    return (None, from_header.strip() or None)


def _call_with_backoff(method, **kwargs):
    """Call a Gmail API method with exponential backoff on rate limit errors."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return method(**kwargs).execute()
        except HttpError as e:
            if e.resp.status == 429 and attempt < max_retries - 1:
                wait = (2 ** attempt) + (time.monotonic() % 1)
                logger.warning("Gmail rate limited, retrying in %.1fs", wait)
                time.sleep(wait)
            else:
                raise
