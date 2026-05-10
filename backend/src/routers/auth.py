"""Google OAuth: combined login + Gmail authorization."""

import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from google_auth_oauthlib.flow import Flow
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from ..config import get_settings
from ..services.gmail_client import TOKEN_PATH

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
settings = get_settings()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
]

SESSION_COOKIE = "trailerpark_session"
SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
STATE_MAX_AGE = 600  # 10 minutes


def _get_serializer() -> URLSafeTimedSerializer:
    secret = settings.SESSION_SECRET
    if not secret:
        raise RuntimeError("SESSION_SECRET must be set")
    return URLSafeTimedSerializer(secret)


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
    return Flow.from_client_config(client_config, SCOPES, redirect_uri=redirect_uri)


def verify_session(request: Request) -> str | None:
    """Verify the session cookie. Returns the email if valid, None otherwise."""
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return None
    try:
        data = _get_serializer().loads(cookie, max_age=SESSION_MAX_AGE)
        return data.get("email")
    except (BadSignature, SignatureExpired):
        return None


def set_session_cookie(response: Response, email: str):
    """Set a signed session cookie on the response."""
    serializer = _get_serializer()
    value = serializer.dumps({"email": email, "t": int(time.time())})
    response.set_cookie(
        SESSION_COOKIE,
        value,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.base_url.startswith("https"),
        samesite="lax",
        path="/",
    )


@router.get("/auth/login")
def login():
    """Start the Google OAuth flow — redirects to Google's consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    redirect_uri = f"{settings.base_url}/api/auth/callback"
    flow = _build_flow(redirect_uri)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    # Include the PKCE code_verifier in the signed state token
    state = _get_serializer().dumps({
        "purpose": "oauth",
        "cv": flow.code_verifier,
    })

    # Replace the state parameter in the URL
    from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params["state"] = [state]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    auth_url = urlunparse(parsed._replace(query=new_query))

    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Handle the OAuth callback from Google."""
    # Handle user cancellation or Google errors
    if error:
        logger.warning("OAuth error from Google: %s", error)
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Verify signed state token
    try:
        state_data = _get_serializer().loads(state, max_age=STATE_MAX_AGE)
        if state_data.get("purpose") != "oauth":
            raise BadSignature("wrong purpose")
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    # Exchange code for tokens (restore PKCE code_verifier from state)
    redirect_uri = f"{settings.base_url}/api/auth/callback"
    flow = _build_flow(redirect_uri)
    flow.code_verifier = state_data.get("cv")
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Verify the ID token and extract email
    try:
        id_info = google_id_token.verify_oauth2_token(
            creds.id_token,
            GoogleRequest(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.error("ID token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Identity verification failed")

    email = id_info.get("email", "").strip().lower()
    email_verified = id_info.get("email_verified", False)

    if not email_verified:
        raise HTTPException(status_code=401, detail="Email not verified by Google")

    # Check against allowlist
    allowed = (settings.ALLOWED_EMAIL or "").strip().lower()
    if not allowed:
        raise HTTPException(status_code=500, detail="ALLOWED_EMAIL not configured")
    if email != allowed:
        logger.warning("Unauthorized login attempt from: %s", email)
        raise HTTPException(status_code=403, detail="This Google account is not authorized")

    # Check that gmail.readonly was actually granted
    granted_scopes = creds.scopes or []
    if "https://www.googleapis.com/auth/gmail.readonly" not in granted_scopes:
        logger.warning("Gmail scope not granted by user")
        raise HTTPException(
            status_code=400,
            detail="Gmail read access is required. Please try again and grant all permissions.",
        )

    # Save Gmail credentials for background syncing
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    if os.name != "nt":
        TOKEN_PATH.chmod(0o600)

    logger.info("User authenticated and Gmail authorized: %s", email)

    # Set session cookie and redirect to app
    response = RedirectResponse(settings.base_url + "/", status_code=302)
    set_session_cookie(response, email)
    return response


@router.get("/auth/status")
def auth_status(request: Request):
    """Check authentication and Gmail connection status."""
    email = verify_session(request)
    from ..services.gmail_client import is_gmail_configured, get_credentials

    gmail_connected = is_gmail_configured()
    gmail_healthy = False
    if gmail_connected:
        creds = get_credentials()
        gmail_healthy = creds is not None and creds.valid

    return {
        "authenticated": email is not None,
        "email": email,
        "gmail_connected": gmail_connected,
        "gmail_healthy": gmail_healthy,
    }


@router.get("/auth/logout")
def logout():
    """Clear the session cookie."""
    response = RedirectResponse(settings.base_url + "/api/auth/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
