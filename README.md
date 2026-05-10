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

## Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API key
- Google Cloud project with Gmail API enabled

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/accorvin/trailerpark.git
cd trailerpark
cp backend/.env.example backend/.env
# Edit backend/.env — set OPENAI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

### 2. Google Cloud setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Gmail API** (APIs & Services → Library → search "Gmail API")
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Application type: **Desktop app**
7. Copy the **Client ID** and **Client Secret** into your `.env` file

**Important**: By default, Google OAuth apps are in "Testing" mode and refresh tokens expire after 7 days. To avoid this, go to the **OAuth consent screen** and publish the app. You'll see an "unverified app" warning during sign-in, which is fine for personal use.

### 3. Install dependencies

```bash
cd backend && uv sync && uv sync --extra dev
cd ../frontend && npm install
```

### 4. Set up the database

```bash
cd backend && uv run alembic -c alembic/alembic.ini upgrade head
```

### 5. Authenticate with Gmail

```bash
cd backend && uv run python -m src.setup_gmail
```

This opens a browser window for one-time OAuth consent. The token is saved locally at `backend/data/gmail_token.json`.

### 6. Run

```bash
cd backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 (API docs at http://localhost:8000/docs)

### Development mode

Run backend and frontend separately for hot-reload:

```bash
# Terminal 1: Backend
cd backend && uv run uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Frontend dev server runs on http://localhost:5173 with API proxy to port 8000.

### Seed data for testing

```bash
cd backend && uv run python -m src.seed
```

## Gmail Setup

The app connects directly to Gmail using OAuth. Set up a forwarding rule or filter in Gmail to label relevant broker emails, then configure `GMAIL_QUERY` in `.env` to target that label:

```env
GMAIL_QUERY=label:TrailerPark
```

By default, the app scans `label:inbox`. On the first sync, it looks back 30 days (configurable via `GMAIL_INITIAL_SYNC_DAYS`).

Use the **Sync Now** button in the dashboard or `POST /api/emails/sync` to trigger an immediate sync.

## Running Tests

```bash
cd backend
uv run pytest                          # All tests
uv run pytest -x -v                    # Stop on first failure, verbose
uv run pytest tests/test_llm_parser.py # Specific test file
```

## Database Backup & Restore

Daily backups are saved to `backend/data/backups/` (7-day rolling).

To restore from a backup:
```bash
cp backend/data/backups/trailerpark-YYYY-MM-DD.db backend/data/trailerpark.db
# Restart the app
```

## Configuration

All settings are in `backend/.env`. See `backend/.env.example` for available options.

Key settings:
- `OPENAI_API_KEY` — OpenAI API key (required)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth credentials (required)
- `GMAIL_QUERY` — Gmail search query to filter emails (default: `label:inbox`)
- `GMAIL_INITIAL_SYNC_DAYS` — How far back to sync on first run (default: 30)
- `SCAN_INTERVAL_MINUTES` — How often to scan for new emails (default: 5)
- `ARCHIVE_DAYS` — Days before auto-archiving (default: 20)
- `DEAL_THRESHOLD` — Price difference threshold for deals in dollars (default: 10000)
