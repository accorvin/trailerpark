# TrailerPark — Implementation Plan

## Summary of Requirements

| Decision | Choice |
|---|---|
| LLM Provider | OpenAI GPT-4o-mini for classification, GPT-4o for extraction + vision |
| Email Source | Power Automate saves emails to OneDrive → syncs to local folder → app scans folder |
| Frontend | React + Vite + TailwindCSS (custom components, no UI library) |
| Deploy OS | Windows (office computer) |
| Auth | None (local single-user) |
| Image emails | Occasional (<20%) — vision parsing in Phase 3 |
| De-duplication | ~1 in 5 listings — moderate priority, Phase 6 |
| Auto-start | Optional — provide both manual script and Windows Task Scheduler setup |

All four feature areas (ingestion, deal detection, matching, dashboard) are equally important. The plan sequences them by dependency: ingestion first, then parsing, then detection/matching, then dashboard.

---

## Project Structure

```
trailerpark/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entrypoint
│   │   ├── config.py                 # Settings from .env
│   │   ├── database.py               # SQLite connection + session
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── listings.py           # GET /listings, GET /listings/{id}
│   │   │   ├── buyers.py             # GET /buyers, GET /buyers/{id}
│   │   │   ├── deals.py              # GET /deals
│   │   │   ├── matches.py            # GET /matches
│   │   │   ├── benchmarks.py         # CRUD /benchmarks
│   │   │   ├── emails.py             # GET /emails (debug/admin view)
│   │   │   ├── attachments.py        # GET /attachments/{id}/file
│   │   │   └── stats.py              # GET /stats (dashboard summary)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── email_ingestion.py    # Local folder scanner for OneDrive-synced emails
│   │   │   ├── attachment_extractor.py # PDF/Excel text extraction
│   │   │   ├── llm_parser.py         # OpenAI calls for classification + extraction
│   │   │   ├── deal_detector.py      # Pricing comparison + deal flagging
│   │   │   ├── matcher.py            # Buyer-seller matching algorithm
│   │   │   ├── archiver.py           # 20-day auto-archive logic
│   │   │   ├── deduplicator.py       # Duplicate listing detection
│   │   │   └── backup.py            # DB backup + attachment cleanup
│   │   ├── seed.py                  # Seed script for dev/testing
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── scheduler.py          # APScheduler setup (email poll, archive, etc.)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Fixtures: test DB, mock OpenAI, sample email dirs
│   │   ├── test_llm_parser.py
│   │   ├── test_deal_detector.py
│   │   ├── test_matcher.py
│   │   ├── test_archiver.py
│   │   ├── test_deduplicator.py
│   │   ├── test_routers/
│   │   │   ├── test_listings.py
│   │   │   ├── test_deals.py
│   │   │   ├── test_matches.py
│   │   │   └── test_benchmarks.py
│   │   └── fixtures/
│   │       ├── sample_email_dirs/    # Sample OneDrive email folders for testing
│   │       ├── sample_pdf.pdf        # Test PDF attachment
│   │       └── sample_excel.xlsx     # Test Excel attachment
│   ├── alembic/
│   │   ├── env.py
│   │   ├── versions/                 # Migration scripts
│   │   └── alembic.ini
│   ├── pyproject.toml
│   ├── .env.example
│   └── data/
│       ├── trailerpark.db            # SQLite database (gitignored)
│       ├── attachments/              # Downloaded attachment files (gitignored)
│       ├── logs/                     # Rotating log files (gitignored)
│       └── backups/                  # Rolling daily DB backups (gitignored)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js            # TailwindCSS v3 config
│   ├── postcss.config.js             # PostCSS config (required for Tailwind v3)
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts             # Fetch wrapper for backend API
│   │   ├── components/
│   │   │   ├── Layout.tsx            # Shell: sidebar + header + main
│   │   │   ├── ListingCard.tsx       # Card for a single listing
│   │   │   ├── ListingDetail.tsx     # Full detail view (modal or page)
│   │   │   ├── BuyerCard.tsx         # Card for a buyer request
│   │   │   ├── MatchCard.tsx         # Buyer-seller match pair card
│   │   │   ├── DealBadge.tsx         # "Deal: $X below market" badge
│   │   │   ├── FilterBar.tsx         # Make/model/year/price/type filters
│   │   │   ├── SearchInput.tsx       # Free-text search box
│   │   │   ├── BenchmarkForm.tsx     # Create/edit price benchmark
│   │   │   ├── StatsBar.tsx          # Summary stats (active listings, deals, etc.)
│   │   │   └── Pagination.tsx        # Pagination controls
│   │   ├── pages/
│   │   │   ├── DealsPage.tsx         # Deals feed
│   │   │   ├── ListingsPage.tsx      # All active listings
│   │   │   ├── BuyersPage.tsx        # Buyer requests + inline matches
│   │   │   ├── MatchesPage.tsx       # Dedicated match pairs view
│   │   │   ├── BenchmarksPage.tsx    # Manage price benchmarks
│   │   │   └── ArchivePage.tsx       # Archived listings
│   │   ├── hooks/
│   │   │   ├── useListings.ts        # Data fetching hook for listings
│   │   │   ├── useDeals.ts
│   │   │   ├── useMatches.ts
│   │   │   └── useBenchmarks.ts
│   │   └── types/
│   │       └── index.ts              # TypeScript types mirroring backend schemas
│   └── public/
│       └── favicon.ico
├── scripts/
│   ├── start.bat                     # Windows startup script (runs backend + frontend)
│   ├── start.sh                      # Unix startup script
│   ├── setup.bat                     # First-time setup (install deps, init DB)
│   └── install-task-scheduler.ps1    # Optional: register as Windows scheduled task
├── .gitignore
├── PLAN.md
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## Phase 1: Foundation

### 1.1 Project Scaffolding

- Initialize `backend/` with `uv init` and `pyproject.toml`
- Initialize `frontend/` with `npm create vite@latest` (React + TypeScript template)
- Set up TailwindCSS in frontend
- Create `.gitignore` (Python, Node, SQLite DB, `data/attachments/`, `data/logs/`, `data/backups/`, `.env`)
- Create `.env.example` with all required config keys

### 1.2 Database Schema + Migrations

- Use **SQLAlchemy 2.0** ORM in **synchronous mode** (simpler and fewer footguns with SQLite for a single-user app; FastAPI endpoints use `def` not `async def` for DB access)
- Use **Alembic** for schema migrations
- Tables: `emails`, `listings`, `buyer_requests`, `price_benchmarks`, `attachments`, `matches`
- Initial migration creates all tables per the data model in PLAN.md
- **SQLite WAL mode**: `database.py` sets `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` on every connection via SQLAlchemy event listener. This prevents "database is locked" errors when APScheduler background jobs write to the DB while the API is handling reads.
- **SQLite note on Windows**: The DB file MUST be on a local drive, not a network share. SQLite file locking on Windows over network drives is unreliable.
- **emails.id**: The `emails` table PK is the OneDrive folder path relative to `EMAIL_DIR` (e.g., `2026-05/2026-05-09T08-30-00`). Timestamp-only folder names avoid filesystem-illegal characters. Human-readable and globally unique.
- **Price columns**: PLAN.md uses `DECIMAL` type, but SQLite stores these as `REAL` (64-bit float). SQLAlchemy's `Numeric` type handles the mapping. For deal detection price comparisons, use integer cents internally to avoid floating-point drift, or accept ~$0.01 precision loss (acceptable for $10k+ deal thresholds).

#### Additional table: `matches`

| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-increment |
| buyer_request_id | INTEGER (FK) | The buyer request |
| listing_id | INTEGER (FK) | The matched listing |
| score | FLOAT | Match relevance score (0-1) |
| matched_at | DATETIME | When the match was computed |

#### Full-text search: `listings_fts` (FTS5 virtual table)

- FTS5 virtual table indexing: `make`, `model`, `engine_type`, `location`, `description`, `seller_name`
- Created in the initial migration alongside regular tables
- Updated via SQLAlchemy `after_insert` / `after_update` event hooks on `listings`
- Powers the `search` query parameter on listing endpoints — uses `MATCH` queries instead of `LIKE '%term%'`

### 1.3 Config Management

- `config.py` uses Pydantic `BaseSettings` to load from `.env`:
  - `EMAIL_DIR` — **required**, path to the OneDrive-synced folder where Power Automate saves emails (e.g., `C:\Users\broker\OneDrive\TrailerPark`)
  - `OPENAI_API_KEY`
  - `DATABASE_URL` (default: `sqlite:///data/trailerpark.db`)
  - `SCAN_INTERVAL_MINUTES` (default: 5) — how often to scan for new email folders (can be frequent since it's just a local directory scan, not an API call)
  - `ARCHIVE_DAYS` (default: 20)
  - `DEAL_THRESHOLD` (default: 10000)
  - `ATTACHMENT_DIR` (default: `data/attachments`) — where the app copies attachments for its own use
  - `ATTACHMENT_MAX_AGE_DAYS` (default: 90) — delete attachment files for archived listings older than this
  - `LOG_DIR` (default: `data/logs`)
  - `PORT` (default: 8000)
  - `BACKUP_DIR` (default: `data/backups`)
  - `OPENAI_MAX_CONCURRENT` (default: 5) — max concurrent OpenAI API calls to avoid rate limits during catch-up processing
- **Path resolution**: All relative paths (`DATABASE_URL`, `ATTACHMENT_DIR`, `LOG_DIR`, `BACKUP_DIR`) are resolved to absolute paths based on the project root at startup using `pathlib.Path`. `EMAIL_DIR` is stored as-is (absolute path provided by user). All file operations use `pathlib.Path` throughout — never string concatenation with `/`.
- **Attachment paths in DB**: Stored as relative paths (relative to `ATTACHMENT_DIR`) so the app is portable if the directory moves.

---

## Phase 2: Email Ingestion

### 2.1 Power Automate Setup (Broker-Side, One-Time)

The broker (or their IT admin) sets up a Power Automate flow in M365. **No premium license required** — all connectors used (Outlook, OneDrive, data operations) are standard connectors included with M365 Business Basic/Standard.

**Flow steps**:

1. **Trigger**: "When a new email arrives (V3)" — fires on each new email in the broker's inbox
2. **Action**: "Html to text" — converts the HTML email body to plain text (the trigger only provides HTML body and a truncated 255-char `bodyPreview`, so this conversion is required for reliable LLM parsing)
3. **Action**: "Compose" — build a JSON object containing:
   - `from_address`, `from_name` (from trigger outputs)
   - `subject` (from trigger outputs)
   - `received_at` (from trigger's `receivedDateTime`)
   - `body_text` (from the Html-to-text output)
   - `body_html` (from trigger's `body`)
4. **Action**: "Create file" in OneDrive — save the composed JSON as `metadata.json` at path:
   `/TrailerPark/{formatDateTime(triggerOutputs()?['receivedDateTime'],'yyyy-MM')}/{formatDateTime(triggerOutputs()?['receivedDateTime'],'yyyy-MM-ddTHH-mm-ss')}/metadata.json`
   - **Monthly parent folders** (e.g., `/TrailerPark/2026-05/`) prevent OneDrive sync from hitting the 300,000-item limit (~500 items/day would approach the limit in 1-2 years with flat structure)
   - **Timestamp-only folder names** (e.g., `2026-05-09T08-30-00`) avoid filename sanitization issues — email subjects can contain `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` which are illegal in OneDrive paths. The subject is stored only inside `metadata.json`.
5. **Action**: "Apply to each" — loop over the trigger's `attachments` array:
   - **Condition**: Filter out inline attachments (`IsInline` equals `false`) — this skips email signature images (logos, social icons, etc.) which appear as attachments but aren't useful content
   - **Action**: "Create file" — save each non-inline attachment to the same folder with its original filename
6. OneDrive desktop sync automatically mirrors this to the local Windows machine

**Expected folder structure on disk**:
```
C:\Users\broker\OneDrive\TrailerPark\
├── 2026-05/
│   ├── 2026-05-09T08-30-00/
│   │   ├── metadata.json
│   │   ├── inventory.pdf
│   │   └── photo1.jpg
│   ├── 2026-05-09T09-15-00/
│   │   ├── metadata.json
│   │   └── specs.xlsx
│   └── ...
├── 2026-06/
│   └── ...
└── ...
```

A step-by-step setup guide with screenshots will be provided in the README for the broker to follow.

### 2.2 Local Directory Scanner (`email_ingestion.py`)

- Scans `EMAIL_DIR` for **monthly subdirectories** (e.g., `2026-05/`), then scans each month folder for **email subdirectories** (e.g., `2026-05-09T08-30-00/`). This two-level scan matches the Power Automate folder structure.
- Only scans the current month and previous month's folders (no need to re-scan old months where all emails are already processed)
- For each email subdirectory found:
  1. Construct the email ID as `{month}/{timestamp}` (e.g., `2026-05/2026-05-09T08-30-00`) — globally unique
  2. Check if the email ID already exists in the `emails` table → **skip if present** (idempotency)
  3. Read `metadata.json` → parse into email record
  4. Inventory all other files in the folder as attachments
  5. Copy attachment files to `ATTACHMENT_DIR/{month}/{timestamp}/` (the app's own attachment storage, separate from OneDrive)
  6. Run the full ingestion pipeline: classify → extract → store
- **Idempotency**: The folder path serves as the email's unique ID. Since folders persist on disk, re-scanning always finds the same set. The DB check ensures each folder is processed exactly once.
- **Crash recovery**: If the app crashes mid-processing, the folder remains on disk and hasn't been recorded in the DB, so it will be re-processed on the next scan. No data loss.
- **No pagination concerns**: Local directory listing returns all entries at once — no API pagination to handle.
- **Transaction wrapping**: Each email folder's full pipeline (classify → extract → store listings/buyers) runs in a single DB transaction. If any step fails, the entire email is rolled back and marked as `classification = "parse_error"` for investigation.
- **Rate limiting**: When processing a backlog (e.g., first run with hundreds of folders), throttle OpenAI calls with a semaphore (`OPENAI_MAX_CONCURRENT`, default 5) to avoid hitting rate limits.

### 2.3 Attachment Text Extraction (`attachment_extractor.py`)

- PDF: Use `pymupdf` (aka `fitz`) to extract text from all pages
- Excel: Use `openpyxl` to read all cells, concatenate as text
- Images: Store path for later vision processing (Phase 3)
- **Inline image detection**: Although the Power Automate flow filters out `IsInline` attachments, as a fallback the extractor also skips image files smaller than 10 KB (likely signature icons/logos). Larger images are kept for potential vision processing.
- Store extracted text in `attachments.extracted_text`

### 2.4 Email Classification (`llm_parser.py` — classification only in Phase 2)

- Send email subject + body + attachment text to **GPT-4o-mini** (classification is a simple task; using mini saves ~90% on this step)
- System prompt classifies as: `seller_listing`, `buyer_request`, or `irrelevant`
- Store classification in `emails.classification`
- Irrelevant emails are stored but not further processed

### 2.5 Scheduler (`scheduler.py`)

- Use **APScheduler** `BackgroundScheduler` (synchronous, matches sync SQLAlchemy choice) running in-process with FastAPI via lifespan
- Job: `scan_emails` — runs every `SCAN_INTERVAL_MINUTES` (default 5) — scans local OneDrive folder for new email directories
- Job: `archive_old` — runs daily, archives listings older than `ARCHIVE_DAYS` (archiver logic built here in Phase 2, not deferred to Phase 6)
- Job: `backup_db` — runs daily, backs up the SQLite database (see Backup Strategy below)
- Job: `cleanup_attachments` — runs daily, deletes attachment files for archived listings older than `ATTACHMENT_MAX_AGE_DAYS`
- On startup, run an initial scan immediately

### 2.6 Auto-Archiving (`archiver.py`)

- Simple service built in Phase 2 alongside the scheduler (the scheduler references it, so they must exist together)
- Any listing with `first_seen_at` older than `ARCHIVE_DAYS` (default 20): set `is_archived = True`, `archived_at = now()`
- Buyer requests also archived after `ARCHIVE_DAYS`
- Runs as a daily scheduled job via APScheduler

---

## Phase 3: Parsing Engine

### 3.1 Structured Data Extraction (`llm_parser.py`)

- For emails classified as `seller_listing`:
  - Send body + attachment text to **GPT-4o** with structured extraction prompt
  - Prompt requests JSON output with: make, model, year, mileage, price, location, engine_type, condition, quantity, vehicle_type, seller_name, seller_contact, description
  - Use OpenAI's **`response_format: { type: "json_schema" }`** (structured outputs) — not just `json_object`. This validates the response against a defined schema, catching missing/wrong-typed fields at the API level rather than in our code.
  - Handle multi-vehicle emails: one email may list multiple trucks — extract as array
  - **Large email chunking**: For emails listing 20+ vehicles, split into chunks of ~10 vehicles each and make separate LLM calls. This prevents unreliable extraction from very long outputs and avoids token limit truncation.
  - **Post-extraction validation**: Validate each extracted listing with a Pydantic model before DB insert. Log and skip invalid entries rather than crashing. Track extraction success rate per email.
  - Create one `listings` row per vehicle extracted

- For emails classified as `buyer_request`:
  - Extract: vehicle_type, make, model, year_min, year_max, mileage_max, price_min, price_max, location, engine_type, buyer_name, buyer_contact, description
  - **Multi-request handling**: A buyer may request multiple different vehicle types in one email (e.g., "looking for a 2022+ Cascadia AND a 53ft reefer trailer"). Extract as array, create one `buyer_requests` row per distinct request.
  - Same structured outputs schema validation as seller extraction

### 3.2 Vision Fallback

- For image attachments where no text was extracted from the email body or other attachments:
  - Send images to GPT-4o vision endpoint
  - Same extraction prompts as text, but with image input
  - Apply to ~20% of emails that are image-heavy

### 3.3 LLM Prompt Strategy

Three prompt templates, all using system + user message pattern:

1. **Classification prompt** (GPT-4o-mini): Short, returns one of three labels. Includes examples of each category. ~500 input tokens, ~10 output tokens per call.
2. **Seller extraction prompt** (GPT-4o): Detailed schema description with field-by-field instructions. Handles edge cases (price "call for pricing" → null, multiple units, etc.). Uses `response_format: { type: "json_schema" }` with a defined schema. Returns JSON array.
3. **Buyer extraction prompt** (GPT-4o): Similar structure, extracts ranges and preferences. Returns JSON array (not object — supports multi-request buyers).

All prompts stored as constants in `llm_parser.py`. Temperature: 0 for deterministic extraction.

**Revised cost estimate** (corrected from original):
- Classification: 100 emails/day × 500 input tokens × $0.15/1M = ~$0.23/month (GPT-4o-mini)
- Extraction: ~70 emails/day (after filtering irrelevant) × 2,500 input + 500 output tokens × GPT-4o pricing ($2.50/$10 per 1M) = ~$24/month
- Vision fallback (~14 emails/day): ~$8/month
- **Total: ~$30-35/month** (not $10-25 as originally estimated in PLAN.md)

---

## Phase 4: Deal Detection & Matching

### 4.1 Manual Benchmarks CRUD (`benchmarks.py` router)

- `POST /benchmarks` — create a new benchmark
- `GET /benchmarks` — list all benchmarks
- `PUT /benchmarks/{id}` — update a benchmark
- `DELETE /benchmarks/{id}` — delete a benchmark
- Benchmark matching: find the most specific benchmark that matches a listing's specs. **Specificity ranking**: count the number of non-null fields in the benchmark (make, model, year range, mileage range). The benchmark with the most non-null fields that all match the listing wins. Ties broken by narrower year/mileage range.

### 4.2 Auto-Computed Pricing (`deal_detector.py`)

- Group listings by: `vehicle_type + make + model + year_bucket + mileage_bucket`
  - Year bucket: 5-year ranges (e.g., 2020-2024)
  - Mileage bucket: 100k ranges (e.g., 300k-400k)
- Compute median price per group when group has >= 5 data points
- Manual benchmarks override auto-computed when both exist

### 4.3 Deal Flagging

- After each new listing is ingested, compare price against:
  1. Manual benchmark (if exists for this spec)
  2. Auto-computed median (if >= 5 data points)
- If listing price is >= `DEAL_THRESHOLD` below benchmark: set `is_deal = True`, `deal_savings = benchmark - price`
- Re-run deal detection nightly (benchmarks and medians change as data accumulates)

### 4.4 Buyer-Seller Matching (`matcher.py`)

- For each active (non-archived) buyer request, score against all active listings:
  - **vehicle_type match**: required (no match if different)
  - **make match**: +0.15 if matches
  - **model match**: +0.25 if matches (model is the strongest signal)
  - **year in range**: +0.2 if listing year within buyer's year_min-year_max
  - **mileage under max**: +0.15 if listing mileage <= buyer's mileage_max
  - **price in range**: +0.2 if listing price within buyer's price_min-price_max
  - **engine match**: +0.05 if matches
- **Threshold**: Store matches with score >= **0.6** in `matches` table. This requires at least 3 substantive criteria to match (e.g., model + year + price), preventing garbage matches like "same make + same engine" without model/year/price alignment.
- **Incremental matching**: After each ingestion cycle, only match *new* listings against existing buyers and *new* buyers against existing listings. Full re-matching runs on the nightly job only (handles cases where listings/buyers were updated).

---

## Phase 5: Web Dashboard

### 5.1 API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/listings` | Active listings, filterable + searchable + paginated |
| GET | `/api/listings/{id}` | Single listing detail with email + attachments |
| GET | `/api/deals` | Listings where `is_deal = True`, sorted by `deal_savings` desc |
| GET | `/api/buyers` | Active buyer requests |
| GET | `/api/buyers/{id}` | Buyer detail with matched listings |
| GET | `/api/matches` | All buyer-seller match pairs, sorted by score |
| GET | `/api/benchmarks` | All price benchmarks |
| POST | `/api/benchmarks` | Create benchmark |
| PUT | `/api/benchmarks/{id}` | Update benchmark |
| DELETE | `/api/benchmarks/{id}` | Delete benchmark |
| GET | `/api/stats` | Summary: active listings count, deals count, buyers count, matches count, attachment storage bytes |
| GET | `/api/archive` | Archived listings |
| GET | `/api/emails` | Raw emails (debug view) |
| GET | `/api/attachments/{id}/file` | Serve an attachment file by attachment ID (returns the binary file with correct Content-Type) |

**Query parameters** for listing endpoints:
- `vehicle_type`, `make`, `model`, `year_min`, `year_max`, `price_min`, `price_max`, `mileage_max`, `engine_type`, `location`, `search` (free-text FTS5 query), `page`, `per_page`

### 5.2 Frontend Pages

| Page | Route | Description |
|---|---|---|
| Deals | `/` (home) | Deal cards sorted by savings. Each shows make/model/year, price, savings badge, seller. |
| Listings | `/listings` | All active listings with FilterBar. Sortable by price, date, year. |
| Buyers | `/buyers` | Buyer request cards. Each shows specs wanted + inline matched listings. |
| Matches | `/matches` | Side-by-side buyer request ↔ listing pairs. Sorted by match score. |
| Benchmarks | `/benchmarks` | Table of benchmarks with add/edit/delete. |
| Archive | `/archive` | Archived listings, same layout as Listings. |
| Detail | `/listings/:id` | Full listing detail: all fields, original email body, attachment links. |

### 5.3 Frontend Architecture

- **Routing**: React Router v6 (pinned to v6.x — v7 is a Remix rewrite with a different API)
- **Data fetching**: Custom hooks using `fetch` (no heavy state library needed for single-user app)
- **Styling**: TailwindCSS v3 utility classes (pinned to v3.x — v4 uses CSS-based config, not `tailwind.config.js`)
- **Layout**: Sidebar navigation (Deals, Listings, Buyers, Matches, Benchmarks, Archive) + main content area
- **Responsive**: Not critical (desktop-only office computer) but basic responsive layout for comfort

### 5.4 Serving Strategy

- In development: Vite dev server (port 5173) proxying API to FastAPI (port 8000). The Vite proxy config handles CORS in dev mode — no separate CORS middleware needed.
- In production: `vite build` produces static files → FastAPI serves them via `StaticFiles` mount. Since frontend and API are same-origin, no CORS issues.
- Single process serves both API and frontend
- **CORS note for dev**: Add `CORSMiddleware` to FastAPI for development only (when Vite dev server is on a different port). Disable in production since everything is same-origin.

---

## Phase 6: Polish

### 6.1 De-Duplication (`deduplicator.py`)

- After each new listing is stored, check for potential duplicates:
  - Same make + model + year + similar mileage (within 5%) + similar price (within 10%)
  - OR same VIN if present (strongest signal)
  - **Null price handling**: If either listing has a null price (e.g., "call for pricing"), skip the price similarity check and require make + model + year + mileage match instead.
  - **Cross-seller duplicates**: For the ~1-in-5 case where different sellers list the same truck, also check for fuzzy description overlap (e.g., shared VIN or unique identifying details) since mileage/price may differ slightly between sellers.
- If duplicate found: link to existing listing (update `last_seen_at`), don't create a new row
- Flag uncertain duplicates for manual review in the dashboard (stretch goal)

### 6.2 Location Normalization

- **Known limitation**: Location is stored as free-text from LLM extraction. "Dallas, TX" vs "Dallas" vs "DFW" are treated as different values, which can break matching and filtering.
- **Phase 6 mitigation**: Normalize to "City, ST" format during extraction by adding a normalization instruction to the LLM prompt (e.g., "Always format location as 'City, ST' using two-letter state codes"). This won't be perfect but handles the common cases.
- **Future enhancement**: Use a geocoding API or state/city lookup table for reliable normalization.

### 6.3 Error Handling & Logging

- Python `logging` module with structured JSON logs
- **Log destinations**:
  - File: `data/logs/trailerpark.log` using `RotatingFileHandler` (10 MB max, keep 5 backups = 50 MB total)
  - Console: also log to stderr when running interactively (for debugging). The `start.bat` script does NOT redirect stdout/stderr — Python logging handles file output.
- Log all LLM calls (prompt hash, response summary, tokens used, latency, cost estimate)
- Log directory scan results (new folders found, folders processed, errors)
- On LLM parse failure: store email with `classification = "parse_error"`, skip, log warning
- On scan error (missing metadata.json, corrupt file): log warning, skip folder, continue
- Logging config set up in `main.py` at startup based on `LOG_DIR` setting

### 6.4 Database Backup Strategy

- **Automated daily backup** via APScheduler job (`backup_db`):
  - Uses SQLite's `VACUUM INTO` command to create a consistent backup file
  - Backup destination: `data/backups/trailerpark-YYYY-MM-DD.db`
  - Keep 7 rolling daily backups; delete older ones automatically
- **Pre-migration backup**: `setup.bat` backs up the DB before running `alembic upgrade head`. If the migration fails, the script restores the backup and displays an error message.
- **Restore procedure**: documented in README — copy a backup file over `data/trailerpark.db` and restart

### 6.5 Attachment Storage Management

- APScheduler job (`cleanup_attachments`) runs daily
- Deletes attachment files for archived listings older than `ATTACHMENT_MAX_AGE_DAYS` (default 90 days)
- The extracted text remains in the DB — only the binary files are deleted
- `/api/stats` endpoint includes a `attachment_storage_bytes` field showing total disk usage of the attachments directory

### 6.6 Startup & Process Management

**`scripts/setup.bat`**:
- Checks Python is installed and on PATH (with helpful error if not)
- Checks Node.js is installed and on PATH
- Checks `uv` is installed
- Verifies `.env` exists and has non-empty values for required keys (`EMAIL_DIR`, `OPENAI_API_KEY`)
- Verifies `EMAIL_DIR` path exists and is accessible on disk
- Installs Python deps with `uv sync`
- Installs Node deps with `npm install`
- Builds frontend with `npm run build`
- Backs up DB (if it exists) before running migrations
- Runs `alembic upgrade head`; if it fails, restores the backup and exits with error
- Exits with a clear error message at each step — no cryptic Python tracebacks

**`scripts/start.bat`**:
- `cd`s to the project directory (so relative paths work regardless of how the script is launched)
- Checks if port is already in use (`netstat -ano | findstr :%PORT%`) and warns the user
- Starts `uvicorn` on the configured `PORT` (default 8000)
- Opens the browser automatically after a short delay (`start http://localhost:%PORT%`)
- Wraps uvicorn in a restart loop: if it crashes, wait 5 seconds and restart (with a max of 5 restarts before giving up and logging a message)

**`scripts/install-task-scheduler.ps1`**:
- Registers a Windows Task Scheduler task to run `start.bat` on user login
- Configures restart on failure (restart interval: 1 minute, max 3 restarts)
- Task runs in the background (no visible console window)

---

## Testability

### Unit Tests

- **LLM parser**: Mock OpenAI responses with fixture JSON. Test that various email formats (single truck, multi-truck, buyer request, irrelevant) are correctly classified and extracted.
- **Deal detector**: Test with known listings and benchmarks. Verify correct deal flagging and savings calculation.
- **Matcher**: Test with known buyer requests and listings. Verify scoring and threshold behavior.
- **Archiver**: Test 20-day cutoff logic.
- **De-duplicator**: Test duplicate detection with near-match listings.

### Integration Tests

- **API routes**: Use FastAPI's `TestClient` with a test SQLite database. Test CRUD operations, filtering, pagination.
- **Email ingestion**: Create sample email directory structures in `tests/fixtures/sample_email_dirs/` with `metadata.json` and sample attachments. Test full pipeline from folder scan → classification → extraction → DB storage. No API mocking needed — just filesystem fixtures.

### Running Tests

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest tests/test_llm_parser.py  # Run specific test file
uv run pytest -x -v              # Stop on first failure, verbose
```

### Manual / Local Testing

- Seed script: `python -m src.seed` — creates sample listings, buyers, and benchmarks for dashboard testing without needing real emails
- For ingestion testing: create sample email folders manually in the `EMAIL_DIR` path with `metadata.json` files and sample attachments — no M365 account or Power Automate setup required for dev/testing

---

## Deployability

### Local Development

1. Clone the repo
2. `cd backend && uv sync` — install Python dependencies
3. `cp .env.example .env` — set `EMAIL_DIR` to a local test folder, add `OPENAI_API_KEY`
4. Create sample email folders in `EMAIL_DIR` for testing (see `tests/fixtures/sample_email_dirs/` for examples)
5. `uv run alembic upgrade head` — create/migrate database
6. `cd frontend && npm install && npm run dev` — start frontend dev server
7. `cd backend && uv run uvicorn src.main:app --reload` — start backend

### Production (Office Computer)

1. Run `scripts/setup.bat` once (installs everything, builds frontend, migrates DB)
2. Run `scripts/start.bat` to start (or install Task Scheduler for auto-start)
3. Open `http://localhost:8000` in browser

### No CI/CD Required

This is a single-user local app. No CI/CD pipeline needed. The broker (or whoever maintains the machine) runs `git pull && scripts/setup.bat` to update.

---

## Files Created Table

| File | Phase | Purpose |
|---|---|---|
| `backend/pyproject.toml` | 1 | Python project config + dependencies |
| `backend/.env.example` | 1 | Template for environment variables |
| `backend/src/__init__.py` | 1 | Package init |
| `backend/src/main.py` | 1 | FastAPI app, startup events, static file mount |
| `backend/src/config.py` | 1 | Pydantic BaseSettings config |
| `backend/src/database.py` | 1 | SQLite engine + session factory |
| `backend/src/models.py` | 1 | SQLAlchemy ORM models (all tables) |
| `backend/src/schemas.py` | 1 | Pydantic schemas for API requests/responses |
| `backend/alembic/env.py` | 1 | Alembic migration config |
| `backend/alembic/alembic.ini` | 1 | Alembic settings |
| `backend/alembic/versions/001_initial.py` | 1 | Initial DB migration |
| `backend/src/services/__init__.py` | 2 | Package init |
| `backend/src/services/email_ingestion.py` | 2 | Local OneDrive folder scanner + attachment copying |
| `backend/src/services/attachment_extractor.py` | 2 | PDF/Excel text extraction |
| `backend/src/services/llm_parser.py` | 2-3 | OpenAI classification + extraction |
| `backend/src/tasks/__init__.py` | 2 | Package init |
| `backend/src/tasks/scheduler.py` | 2 | APScheduler job definitions |
| `backend/src/services/deal_detector.py` | 4 | Pricing + deal flagging |
| `backend/src/services/matcher.py` | 4 | Buyer-seller matching |
| `backend/src/routers/__init__.py` | 5 | Package init |
| `backend/src/routers/listings.py` | 5 | Listings API endpoints |
| `backend/src/routers/buyers.py` | 5 | Buyers API endpoints |
| `backend/src/routers/deals.py` | 5 | Deals API endpoints |
| `backend/src/routers/matches.py` | 5 | Matches API endpoints |
| `backend/src/routers/benchmarks.py` | 4-5 | Benchmarks CRUD endpoints |
| `backend/src/routers/emails.py` | 5 | Emails debug endpoint |
| `backend/src/routers/stats.py` | 5 | Dashboard summary stats |
| `backend/src/services/archiver.py` | 2 | Auto-archive logic (built with scheduler) |
| `backend/src/services/deduplicator.py` | 6 | Duplicate detection |
| `backend/src/services/backup.py` | 6 | DB backup + attachment cleanup |
| `backend/src/seed.py` | 1 | Seed script for dev/testing |
| `backend/src/routers/attachments.py` | 5 | Attachment file serving endpoint |
| `backend/tests/conftest.py` | 1+ | Test fixtures |
| `backend/tests/test_llm_parser.py` | 3 | Parser tests |
| `backend/tests/test_deal_detector.py` | 4 | Deal detection tests |
| `backend/tests/test_matcher.py` | 4 | Matching tests |
| `backend/tests/test_archiver.py` | 2 | Archiver tests |
| `backend/tests/test_deduplicator.py` | 6 | Dedup tests |
| `backend/tests/test_routers/*.py` | 5 | API route tests |
| `backend/tests/fixtures/sample_email_dirs/` | 2+ | Sample OneDrive email folder structures for testing |
| `frontend/package.json` | 5 | Node project config |
| `frontend/vite.config.ts` | 5 | Vite config with API proxy |
| `frontend/tailwind.config.js` | 5 | Tailwind config |
| `frontend/postcss.config.js` | 5 | PostCSS config |
| `frontend/tsconfig.json` | 5 | TypeScript config |
| `frontend/index.html` | 5 | HTML entry point |
| `frontend/src/main.tsx` | 5 | React entry point |
| `frontend/src/App.tsx` | 5 | Root component with router |
| `frontend/src/api/client.ts` | 5 | API client |
| `frontend/src/types/index.ts` | 5 | TypeScript type definitions |
| `frontend/src/components/*.tsx` | 5 | UI components (11 files) |
| `frontend/src/pages/*.tsx` | 5 | Page components (6 files) |
| `frontend/src/hooks/*.ts` | 5 | Data fetching hooks (4 files) |
| `scripts/start.bat` | 6 | Windows startup script |
| `scripts/start.sh` | 6 | Unix startup script |
| `scripts/setup.bat` | 6 | Windows setup script |
| `scripts/install-task-scheduler.ps1` | 6 | Windows auto-start setup |
| `.gitignore` | 1 | Git ignore rules |
| `README.md` | 6 | Setup and usage docs |

---

## Key Dependencies

### Backend (`pyproject.toml`)

```
fastapi >= 0.115
uvicorn[standard] >= 0.34
sqlalchemy >= 2.0
alembic >= 1.14
openai >= 1.60
pymupdf >= 1.25
openpyxl >= 3.1
apscheduler >= 3.10, < 4        # v4 has a completely different API
pydantic-settings >= 2.7        # reads .env natively, no python-dotenv needed
pytest >= 8.0
```

### Frontend (`package.json`)

```
react ^19.0.0
react-dom ^19.0.0
react-router-dom ^6.28.0        # pinned to v6.x — v7 is a Remix rewrite
tailwindcss ^3.4.0               # pinned to v3.x — v4 uses CSS-based config
@tailwindcss/forms ^0.5.0
typescript ^5.7.0
vite ^6.0.0
```

---

## UX Recommendation

The dashboard is the primary user-facing surface. I recommend spawning a **UX teammate** to:

1. Review the page layouts and information hierarchy (especially the Deals and Matches pages which are the highest-value views)
2. Design the FilterBar interaction pattern
3. Recommend a visual treatment for deal badges and match scores
4. Ensure the listing detail view surfaces all relevant info without overwhelming

---

## Open Questions / Risks

1. **Power Automate flow setup**: The broker or their IT admin needs to create the Power Automate flow (section 2.1). No premium license required — all connectors are standard (included with M365 Business Basic/Standard). A step-by-step guide with screenshots will be provided in the README. Development and testing can proceed independently using manually-created sample email folders.
2. **OneDrive sync latency**: There may be a delay between Power Automate saving a file to OneDrive and the local desktop client syncing it. Typically 1-5 minutes. Combined with the 5-minute scan interval, worst case is ~10 minutes from email receipt to processing. This is acceptable (broker checks dashboard ~3x/day).
3. **OneDrive sync item limit**: OneDrive has a 300,000-item limit across all synced locations. At ~500 items/day (folders + metadata + attachments), a flat structure would approach the limit in 1-2 years. The monthly parent folder structure (`/TrailerPark/2026-05/`) mitigates this by keeping per-folder item counts manageable, and old months can be unsynced from the desktop client without affecting the app (already processed into the DB).
4. **LLM costs**: Revised estimate is ~$30-35/month at 100 emails/day using GPT-4o-mini for classification + GPT-4o for extraction. Monitor token usage via logged cost estimates. If costs are too high, can switch extraction to GPT-4o-mini (lower accuracy but ~80% cheaper).
5. **LLM extraction accuracy**: The unstructured nature of emails means extraction won't be 100% accurate. Plan to iterate on prompts based on real data. Structured outputs help but don't guarantee semantic correctness.
6. **Multi-vehicle emails**: Some sellers list 20+ trucks in one email. The chunking strategy (10 vehicles per LLM call) mitigates truncation but adds latency. The UI must handle listings linked to the same email.
7. **Complexity vs. value**: This plan has 50+ files across 6 phases. This is appropriate given the requirements (email ingestion, LLM parsing, deal detection, matching, full dashboard), but Phase 1-3 should be prioritized to get value flowing quickly. The broker should see parsed emails in the dashboard as soon as possible, even before deal detection is complete.
8. **`emails.raw_json` column**: The `raw_json` column in the emails table stores the original `metadata.json` content for debugging. At 100 emails/day this is modest (~1-5 KB per email). Unlike full Graph API responses, this is lightweight enough to store by default.
