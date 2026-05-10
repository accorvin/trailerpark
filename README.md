# TrailerPark

A local deal aggregator for commercial truck and trailer brokers. Ingests emails from Gmail, uses OpenAI to classify and extract structured listing data, detects deals against price benchmarks, and matches buyer requests to seller listings.

## Features

- **Gmail Email Ingestion**: Connects to Gmail via OAuth and polls for new emails on a schedule
- **LLM Classification & Extraction**: GPT-4o-mini classifies emails; GPT-4o extracts structured vehicle data
- **Deal Detection**: Flags listings priced significantly below manual or auto-computed benchmarks
- **Buyer-Seller Matching**: Scores buyer requests against active listings by vehicle specs
- **Web Dashboard**: React frontend with deals, listings, buyers, matches, benchmarks, and archive views
- **Auto-Archiving**: Listings older than 20 days are automatically archived
- **De-duplication**: Detects and merges duplicate listings from different sellers

## Deploy to Railway (Recommended)

The easiest way to run TrailerPark — no local install needed.

### 1. Google Cloud setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project, enable the **Gmail API**
3. Configure the **OAuth consent screen** (External, add your Gmail as a test user)
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Application type: **Web application**
7. Add an authorized redirect URI: `https://YOUR-APP.up.railway.app/api/auth/gmail/callback`
   (you'll get your Railway URL in step 2 — come back and update this)
8. Copy the **Client ID** and **Client Secret**

**Important**: Go to **OAuth consent screen → Publish App** to prevent refresh tokens from expiring after 7 days. The "unverified app" warning during sign-in is fine for personal use.

### 2. Deploy on Railway

1. Create a [Railway](https://railway.app) account
2. Click **New Project → Deploy from GitHub Repo** and select this repo
3. Add a **Volume** mounted at `/app/data`
4. Set these **environment variables** in the Railway dashboard:
   - `OPENAI_API_KEY` — your OpenAI API key
   - `GOOGLE_CLIENT_ID` — from step 1
   - `GOOGLE_CLIENT_SECRET` — from step 1
   - `GMAIL_QUERY` — e.g., `from:alex@truthtruckgroup.com`
   - `RAILWAY_RUN_UID` — set to `0` (fixes SQLite permissions on volumes)
5. Railway will auto-build and deploy. Note your app URL (e.g., `https://trailerpark-production-xxxx.up.railway.app`)
6. Go back to Google Cloud Console and add `https://YOUR-APP.up.railway.app/api/auth/gmail/callback` as an authorized redirect URI

### 3. Connect Gmail

Visit `https://YOUR-APP.up.railway.app/api/auth/gmail/connect` in your browser. Sign in with the Gmail account that receives the forwarded broker emails. Done — the app will start syncing automatically.

**Cost**: ~$5-8/month on Railway's Hobby plan.

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```bash
git clone https://github.com/accorvin/trailerpark.git
cd trailerpark
cp backend/.env.example backend/.env
# Edit backend/.env — set OPENAI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

For local dev, create a **Desktop app** OAuth client in Google Cloud Console (no redirect URI needed).

```bash
# Install dependencies
cd backend && uv sync --extra dev
cd ../frontend && npm install

# Set up the database
cd ../backend && uv run alembic -c alembic/alembic.ini upgrade head

# Authenticate with Gmail (opens browser)
uv run python -m src.setup_gmail

# Run backend and frontend separately for hot-reload
# Terminal 1:
uv run uvicorn src.main:app --reload --port 8000

# Terminal 2:
cd ../frontend && npm run dev
```

Frontend dev server runs on http://localhost:5173 with API proxy to port 8000.

### Seed data for testing

```bash
cd backend && uv run python -m src.seed
```

### Running tests

```bash
cd backend
uv run pytest                          # All tests
uv run pytest -x -v                    # Stop on first failure, verbose
```

## Gmail Setup

Set up email forwarding from the broker's work email to a Gmail account. Then configure `GMAIL_QUERY` to filter:

```env
GMAIL_QUERY=from:alex@truthtruckgroup.com
```

By default, the app scans `label:inbox`. On the first sync, it looks back 30 days (configurable via `GMAIL_INITIAL_SYNC_DAYS`).

Use the **Sync Now** button in the dashboard or `POST /api/emails/sync` to trigger an immediate sync.

## Database Backup & Restore

Daily backups are saved to `data/backups/` (7-day rolling).

## Configuration

All settings are configured via environment variables (or `backend/.env` for local dev). See `backend/.env.example` for the full list.

Key settings:
- `OPENAI_API_KEY` — OpenAI API key (required)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth credentials (required)
- `GMAIL_QUERY` — Gmail search query to filter emails (default: `label:inbox`)
- `GMAIL_INITIAL_SYNC_DAYS` — How far back to sync on first run (default: 30)
- `SCAN_INTERVAL_MINUTES` — How often to scan for new emails (default: 5)
- `ARCHIVE_DAYS` — Days before auto-archiving (default: 20)
- `DEAL_THRESHOLD` — Price difference threshold for deals in dollars (default: 10000)
