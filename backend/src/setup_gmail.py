"""One-time Gmail OAuth setup.

Usage:
    uv run python -m src.setup_gmail
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from .config import get_settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    settings = get_settings()

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    token_path = settings.data_dir_path / "gmail_token.json"

    if token_path.exists():
        print(f"Gmail token already exists at {token_path}")
        answer = input("Re-authenticate? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    # Build client config from env vars (no secrets file needed)
    client_config = {
        "installed": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\nOpening browser for Gmail authorization...")
    print("(If it doesn't open, check the terminal for a URL to visit)\n")

    creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    # Restrict file permissions (owner read/write only)
    token_path.chmod(0o600)

    print(f"\nGmail authenticated successfully!")
    print(f"Token saved to: {token_path}")
    print("\nYou can now start the app with:")
    print("  uv run uvicorn src.main:app --reload --port 8000")


if __name__ == "__main__":
    main()
