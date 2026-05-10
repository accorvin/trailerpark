# TrailerPark

A local deal aggregator for commercial truck and trailer brokers. Ingests emails via Power Automate + OneDrive sync, uses OpenAI to classify and extract structured listing data, detects deals against price benchmarks, and matches buyer requests to seller listings.

## Features

- **Email Ingestion**: Scans a local OneDrive-synced folder for emails saved by Power Automate
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
- Power Automate flow saving emails to OneDrive (see `docs/power-automate-setup.pdf` or `docs/power-automate-setup.html`)

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url> trailerpark
cd trailerpark
cp backend/.env.example backend/.env
# Edit backend/.env:
#   EMAIL_DIR=C:\Users\broker\OneDrive\TrailerPark  (or local test folder)
#   OPENAI_API_KEY=sk-...
```

### 2. Install and setup

**Windows:**
```bash
scripts\setup.bat
```

**Unix/macOS:**
```bash
cd backend && uv sync && uv sync --extra dev
cd ../frontend && npm install && npm run build
cd ../backend && uv run alembic -c alembic/alembic.ini upgrade head
```

### 3. Run

**Windows:**
```bash
scripts\start.bat
```

**Unix/macOS:**
```bash
cd backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 (API docs available at http://localhost:8000/docs)

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

## Running Tests

```bash
cd backend
uv run pytest                          # All tests
uv run pytest -x -v                    # Stop on first failure, verbose
uv run pytest tests/test_llm_parser.py # Specific test file
```

## Power Automate Setup

See `docs/power-automate-setup.pdf` (or `docs/power-automate-setup.html`) for step-by-step instructions on setting up the M365 Power Automate flow.

The flow saves incoming emails as `metadata.json` files with attachments to OneDrive, organized by month:

```
OneDrive/TrailerPark/
  2026-05/
    2026-05-09T08-30-00/
      metadata.json
      inventory.pdf
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
- `EMAIL_DIR` — Path to OneDrive-synced email folder (required)
- `OPENAI_API_KEY` — OpenAI API key (required)
- `SCAN_INTERVAL_MINUTES` — How often to scan for new emails (default: 5)
- `ARCHIVE_DAYS` — Days before auto-archiving (default: 20)
- `DEAL_THRESHOLD` — Price difference threshold for deals in dollars (default: 10000)

## Auto-Start (Windows)

Run as administrator:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-task-scheduler.ps1
```
