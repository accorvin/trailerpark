"""Web-based Gmail OAuth flow for headless deployments (Railway, VPS, etc.)."""

import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from ..config import get_settings
from ..services.gmail_client import TOKEN_PATH

router = APIRouter(tags=["auth"])
settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# In-memory state store (single-user app, single process)
_pending_states: set[str] = set()


def _build_flow(redirect_uri: str) -> Flow:
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = Flow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)
    return flow


@router.get("/auth/gmail/connect")
def gmail_connect():
    """Start the Gmail OAuth flow — redirects to Google's consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set",
        )

    redirect_uri = f"{settings.base_url}/api/auth/gmail/callback"
    flow = _build_flow(redirect_uri)

    state = secrets.token_urlsafe(32)
    _pending_states.add(state)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )

    return RedirectResponse(auth_url)


@router.get("/auth/gmail/callback")
def gmail_callback(code: str, state: str):
    """Handle the OAuth callback from Google."""
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    _pending_states.discard(state)

    redirect_uri = f"{settings.base_url}/api/auth/gmail/callback"
    flow = _build_flow(redirect_uri)
    flow.fetch_token(code=code)

    creds = flow.credentials

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())

    # Redirect to the app's home page
    return RedirectResponse(settings.base_url + "/")
