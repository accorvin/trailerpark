# Implementation Plan: Jargon Learning, Parse Transparency & Feedback Loop

## Overview

Three interconnected features for TrailerPark that improve LLM extraction quality over time:

1. **Jargon Glossary** — Pre-seeded + user-editable + auto-learned abbreviation dictionary injected into LLM prompts
2. **Parse Transparency** — Side-by-side email/extraction view with field-level source mapping and click-through navigation
3. **User Feedback Loop** — Edit extracted fields, reclassify emails, flag & re-parse; corrections auto-populate the glossary

**Priority order**: Jargon Glossary → Feedback Loop → Parse Transparency

---

## Phase 1: Jargon Glossary

### 1.1 Database Model

**New file**: `src/models.py` (add to existing)

```python
class GlossaryEntry(Base):
    __tablename__ = "glossary_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    abbreviation = Column(String(collation="NOCASE"), nullable=False, unique=True, index=True)  # e.g. "FRL"
    expansion = Column(String, nullable=False)        # e.g. "Freightliner"
    category = Column(String, nullable=True)           # e.g. "make", "model", "engine", "general"
    source = Column(String, nullable=False, default="seed")  # "seed", "user", "auto_learned"
    is_deleted = Column(Boolean, default=False)         # tombstone — user-deleted entries won't be re-seeded
    usage_count = Column(Integer, default=0)            # times matched in emails; used for glossary prompt cap (top N)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

> **Case sensitivity**: The `COLLATE NOCASE` on the `abbreviation` column ensures "FRL", "frl", and "Frl" all resolve to the same entry. All lookups and uniqueness checks are case-insensitive. The `auto_learn_entry()` function normalizes abbreviations to uppercase on insert.

> **Tombstone for deleted entries**: The `is_deleted` flag prevents `POST /api/glossary/seed` from re-adding entries the user intentionally deleted. The seed endpoint skips abbreviations where a tombstoned entry exists. Glossary prompt generation and API listing exclude tombstoned entries.

**Migration**: New Alembic migration to create `glossary_entries` table (with `COLLATE NOCASE` on the unique constraint) and seed initial data.

### 1.2 Seed Data

**New file**: `src/services/glossary_seed.py`

Pre-seeded glossary (~50-100 entries) covering common trucking abbreviations:

| Category | Examples |
|----------|----------|
| Makes | FRL=Freightliner, PB/Pete=Peterbilt, KW=Kenworth, INT/Navistar=International, Volvo=Volvo |
| Models | Casc=Cascadia, T680, 579, VNL, W900, 389 |
| Engines | DD13/DD15=Detroit Diesel, X15=Cummins X15, MX-13=Paccar MX-13, ISX=Cummins ISX |
| Vehicle types | reefer=refrigerated trailer, flatbed, dry van, tanker, stepdeck=step deck |
| Conditions/terms | DOT=Department of Transportation, APU=auxiliary power unit, DPF=diesel particulate filter |
| Units | K=thousand (as in miles or dollars), mi=miles |

Seed data will be inserted **in the Alembic migration itself** (via `op.bulk_insert()`) so it becomes part of version history and is repeatable. The `/api/glossary/seed` endpoint is available for re-seeding defaults later without a new migration.

### 1.3 Glossary Service

**New file**: `src/services/glossary.py`

```python
# Module-level cache
_glossary_cache: str | None = None
_glossary_cache_time: float = 0
GLOSSARY_CACHE_TTL = 300  # 5 minutes

def get_glossary_prompt_section(db: Session) -> str:
    """Build a formatted glossary string for injection into LLM system prompts.

    Results are cached for 5 minutes to avoid repeated DB queries during
    batch email processing. Cache is invalidated on glossary CRUD operations.

    Returns a string capped at the top 200 entries by usage_count to limit
    prompt token overhead (~400-600 tokens for 200 entries).
    """
    # Returns something like:
    # "Common industry abbreviations:\n- FRL = Freightliner\n- PB = Peterbilt\n..."
    # Grouped by category for clarity
    # Excludes is_deleted=True entries

def invalidate_glossary_cache():
    """Called after any glossary CRUD operation to bust the cache."""

def record_abbreviation_match(db: Session, abbreviation: str):
    """Increment usage_count when an abbreviation is found in processed email text."""

def auto_learn_entry(db: Session, abbreviation: str, expansion: str, category: str | None = None):
    """Create or update a glossary entry from a user correction (source='auto_learned').

    Uses INSERT ... ON CONFLICT (upsert) to handle duplicates:
    - If the abbreviation doesn't exist: create with source='auto_learned'
    - If it exists with source='seed': update expansion and set source='auto_learned'
      (user correction overrides seed data)
    - If it exists with source='user': do NOT overwrite (user-defined entries take precedence)
    - Normalizes abbreviation to uppercase before insert
    """
```

> **Conflict resolution policy**: Priority order is `user` > `auto_learned` > `seed`. User-created entries are never overwritten. Auto-learned entries override seed entries. When a conflict occurs on auto-learn, the entry is updated only if the existing source is `seed`. This prevents auto-learning from overriding intentional user definitions.

> **Caching**: The glossary prompt section is cached in-memory with a 5-minute TTL. This avoids hitting the DB on every LLM call during batch processing. The cache is invalidated on any glossary CRUD operation. The prompt is capped at the top 200 entries by `usage_count` (falling back to all entries if fewer than 200 exist) to limit token overhead.

> **`usage_count` purpose**: Used to rank entries for the prompt cap (top N by usage). Also surfaced in the glossary management UI so users can see which abbreviations are most commonly encountered.

### 1.4 LLM Prompt Integration

**Modified file**: `src/services/llm_parser.py`

- `classify_email()`, `extract_listings()`, `extract_buyer_requests()`, and `extract_from_image()` will all accept an optional `glossary_section: str = ""` parameter
- The glossary section is appended to the system prompt:

```
{EXISTING_SYSTEM_PROMPT}

## Industry Abbreviations Reference
The following abbreviations are commonly used in commercial trucking emails:
- FRL = Freightliner
- PB = Peterbilt
...
When you encounter these abbreviations, use the full expanded form in your output.
```

> **`extract_from_image()` included**: Vision-based extraction also uses `SELLER_EXTRACTION_SYSTEM_PROMPT` and will benefit from glossary injection. The glossary section is appended identically.

**Modified file**: `src/services/email_ingestion.py`

- `_process_gmail_message()` calls `get_glossary_prompt_section(db)` which returns a cached result (5-minute TTL), then passes it to all LLM functions. The cache ensures no redundant DB queries across messages processed in the same scan batch.

### 1.5 Glossary API

**New file**: `src/routers/glossary.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/glossary` | List all entries (with optional `?category=` and `?search=` filters) |
| POST | `/api/glossary` | Create a new entry (source="user") |
| PUT | `/api/glossary/{id}` | Update an entry |
| DELETE | `/api/glossary/{id}` | Delete an entry |
| POST | `/api/glossary/seed` | Re-seed default entries (only adds missing ones, doesn't overwrite edits) |

### 1.6 Glossary UI (Frontend)

**New file**: `frontend/src/pages/GlossaryPage.tsx`

- Table view of all glossary entries with columns: Abbreviation, Expansion, Category, Source, Usage Count
- Add/Edit/Delete functionality via modal or inline editing
- Filter by category and search
- Badge showing source (seed / user / auto-learned)

**Modified file**: `frontend/src/App.tsx` — Add route for `/glossary`
**Modified file**: `frontend/src/components/Layout.tsx` — Add nav link

### 1.7 Files Changed (Phase 1)

| File | Action |
|------|--------|
| `src/models.py` | Add `GlossaryEntry` model |
| `src/services/glossary.py` | **New** — glossary service |
| `src/services/glossary_seed.py` | **New** — seed data |
| `src/services/llm_parser.py` | Modify prompts to accept glossary section |
| `src/services/email_ingestion.py` | Pass glossary to LLM calls |
| `src/routers/glossary.py` | **New** — CRUD API |
| `src/schemas.py` | Add `GlossaryEntryResponse`, `GlossaryEntryCreate`, `GlossaryEntryUpdate` |
| `src/main.py` | Register glossary router |
| `alembic/versions/xxx_add_glossary.py` | **New** — migration (creates table + seeds data via `op.bulk_insert()`) |
| `alembic/env.py` | Add `GlossaryEntry` to model imports |
| `frontend/src/pages/GlossaryPage.tsx` | **New** — glossary management UI |
| `frontend/src/hooks/useGlossary.ts` | **New** — API hooks |
| `frontend/src/App.tsx` | Add route |
| `frontend/src/components/Layout.tsx` | Add nav link |

---

## Phase 2: User Feedback Loop

### 2.1 Database Changes

**Modified file**: `src/models.py`

Add to `Listing` model:
```python
user_edited = Column(Boolean, default=False)
user_edited_at = Column(DateTime, nullable=True)
original_extracted_data = Column(Text, nullable=True)  # JSON snapshot — see serialization note below
```

Add to `BuyerRequest` model:
```python
user_edited = Column(Boolean, default=False)
user_edited_at = Column(DateTime, nullable=True)
original_extracted_data = Column(Text, nullable=True)
```

> **`original_extracted_data` serialization**: This stores a JSON snapshot of the entity's extractable fields at the time of first user edit. Serialized via Pydantic's `model_dump(mode="json")` on the corresponding schema (`ListingBase` / `BuyerRequestBase`), which handles `Decimal` → `float` and `datetime` → ISO string conversion. The snapshot is taken only on the first edit (when `user_edited` transitions from `False` to `True`). Shape matches the `ListingBase`/`BuyerRequestBase` schema dict. Exposed in the API via the detail response so the frontend can show original vs. current diffs.

Add to `Email` model:
```python
user_reclassified = Column(Boolean, default=False)
original_classification = Column(String, nullable=True)
reprocessed_at = Column(DateTime, nullable=True)
```

New model for tracking field-level corrections:
```python
class FieldCorrection(Base):
    __tablename__ = "field_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)  # "listing" or "buyer_request"
    entity_id = Column(Integer, nullable=False)
    field_name = Column(String, nullable=False)    # e.g. "make"
    original_value = Column(String, nullable=True)
    corrected_value = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### 2.2 Feedback API

**New file**: `src/routers/feedback.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/api/listings/{id}` | Update listing fields; stores original values, sets `user_edited=True`, records `FieldCorrection`s. `id` is `int`. |
| PATCH | `/api/buyer-requests/{id}` | Same for buyer requests. `id` is `int`. |
| POST | `/api/emails/{id}/reclassify` | Change classification; body: `{"classification": "seller_listing"}`. Triggers re-extraction. **`id` is `str`** (Gmail message ID, not integer). |
| POST | `/api/emails/{id}/reparse` | Flag & re-parse: deletes existing extracted data, re-runs extraction with current glossary. **`id` is `str`**. |
| GET | `/api/feedback/corrections` | List corrections with pagination (`?page=&per_page=`). Returns `PaginatedResponse`. |

> **Path parameter types**: Email endpoints use `id: str` (Gmail message IDs like `"18f2a3b4c5d6e7f8"`), while Listing/BuyerRequest endpoints use `id: int`. FastAPI path parameter type annotations must match.

> **Auth**: All new endpoints are under `/api/*` and are automatically protected by the existing `AuthMiddleware`. No additional authorization layers are needed for this single-user app. The `POST /api/glossary/seed` endpoint is not admin-restricted since there's only one user.

> **Rate limiting on re-parse**: The re-parse and reclassify endpoints each trigger 2-3 OpenAI API calls. To prevent accidental cost spikes, these endpoints will check if the email was already re-parsed within the last 60 seconds (via `reprocessed_at`) and return HTTP 429 if so. This is a simple time-based throttle, not full rate limiting.

**Modified files**: `src/routers/listings.py`, `src/routers/buyers.py` — Add PATCH endpoints (or put them in feedback.py to keep existing routers untouched).

### 2.3 Auto-Learning from Corrections

**Modified file**: `src/services/glossary.py`

When a user edits a field (e.g., changes `make` from "FRL" to "Freightliner"):
1. The PATCH endpoint checks if the original value looks like an abbreviation (short, all-caps or common pattern)
2. If so, calls `auto_learn_entry(db, abbreviation="FRL", expansion="Freightliner", category="make")`
3. The glossary entry is created with `source="auto_learned"`
4. Future emails will benefit from this learned abbreviation

Logic for detecting abbreviation-like corrections:
- The correction is for a **categorizable field only**: `make`, `model`, `engine_type`, `vehicle_type` (NOT `location`, `condition`, `description`, `seller_name`, etc. — these fields commonly have short uppercase values like "TX", "NEW", "DOT" that aren't abbreviations in context)
- Original value is 2-5 characters long (single chars and long strings excluded)
- Original value is all-uppercase or a known abbreviation pattern (e.g., no spaces, no punctuation)
- Corrected value is at least 2x the length of the original
- The abbreviation does not already exist in the glossary with `source="user"` (don't override user entries)

> **False positive mitigation**: The field allowlist is the primary guard. Values like "TX" in the `location` field or "NEW" in the `condition` field won't trigger auto-learning because those fields aren't in the allowlist. For the allowed fields, the length ratio check (2x) prevents cases like correcting "579" to "579 Ultraloft" from being treated as abbreviation expansion.

### 2.4 Re-parse Flow

When a user triggers re-parse on an email:

1. **Acquire `_scan_lock`** (the same lock used by `scan_emails()`) to prevent concurrent processing of the same email by the background scanner
2. Store existing listings/buyer_requests as `original_extracted_data` JSON
3. **Delete associated `Match` rows first** (via ORM cascade — see note below), then delete `Listing` and `BuyerRequest` rows for that email
4. Re-run `classify_email()` and `extract_listings()`/`extract_buyer_requests()` with current glossary
5. Save new extracted data
6. Update `email.reprocessed_at`
7. Release `_scan_lock`

When a user reclassifies an email:

1. **Acquire `_scan_lock`**
2. Store `original_classification`
3. Set `user_reclassified = True`
4. **Delete associated `Match` rows** (via ORM cascade), then delete existing extracted data for old classification
5. Run extraction for new classification
6. Save new extracted data
7. Release `_scan_lock`

> **Concurrency protection**: Both re-parse and reclassify acquire the same `_scan_lock` (from `email_ingestion.py`) to prevent race conditions with the background email scanner. If a scan is in progress, the re-parse endpoint returns HTTP 409 Conflict with a "sync in progress" message rather than blocking.

> **Match data loss warning**: The API response for re-parse/reclassify includes a `matches_deleted: int` count so the frontend can show a warning ("3 matches were removed and will need to be re-generated"). The frontend should show a confirmation dialog before triggering re-parse if the listing/buyer_request has matches.

> **Cascade delete**: Add `cascade="all, delete-orphan"` to the `Listing.matches` and `BuyerRequest.matches` relationships so SQLAlchemy handles match deletion automatically when listings/buyer_requests are deleted via ORM. SQLite foreign key enforcement should also be enabled by adding `event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))` in `src/database.py` if not already present.

> **FTS5 index sync**: The existing `listings_fts` FTS5 virtual table (used by the search endpoint in `listings.py:66-74`) must stay in sync when listings are deleted and recreated during re-parse. If the FTS index uses triggers (SQLite FTS5 content-sync triggers), this happens automatically. If not, the re-parse flow must manually delete from `listings_fts` before deleting listings, and the FTS index will be populated on insert. Verify the current trigger setup during implementation.

### 2.5 Feedback UI (Frontend)

**Modified file**: `frontend/src/components/ListingDetail.tsx`

- Add "Edit" button that makes fields inline-editable
- Add "Save" / "Cancel" buttons when editing
- Show a badge when `user_edited = true`
- Show diff (original vs. current) when hovering over edited fields

**Modified file**: `frontend/src/pages/ListingDetailPage.tsx`

- Add "Re-parse" button
- Add "Reclassify" dropdown (seller_listing / buyer_request / irrelevant)

**New file**: `frontend/src/components/EditableField.tsx` — Reusable inline-edit component

### 2.6 Files Changed (Phase 2)

| File | Action |
|------|--------|
| `src/models.py` | Add fields to Listing, BuyerRequest, Email; add FieldCorrection model |
| `src/routers/feedback.py` | **New** — feedback/correction endpoints |
| `src/routers/listings.py` | Add PATCH endpoint |
| `src/routers/buyers.py` | Add PATCH endpoint |
| `src/schemas.py` | Add update schemas, correction schemas |
| `src/services/glossary.py` | Add auto-learning logic |
| `src/services/email_ingestion.py` | Add reparse/reclassify functions |
| `src/main.py` | Register feedback router |
| `alembic/versions/xxx_add_feedback.py` | **New** — migration |
| `alembic/env.py` | Add `FieldCorrection` to model imports |
| `src/database.py` | Enable SQLite FK enforcement (`PRAGMA foreign_keys=ON`) |
| `frontend/src/components/ListingDetail.tsx` | Add editing, re-parse, reclassify |
| `frontend/src/components/EditableField.tsx` | **New** — inline edit component |
| `frontend/src/pages/ListingDetailPage.tsx` | Add action buttons |
| `frontend/src/hooks/useFeedback.ts` | **New** — API hooks for feedback actions |

---

## Phase 3: Parse Transparency

### 3.1 Database Changes

**Modified file**: `src/models.py`

Add to `Listing` and `BuyerRequest`:
```python
source_mapping = Column(Text, nullable=True)  # JSON: {"make": "found 'FRL' in line 3", "price": "found '$45,000' in line 5", ...}
```

Add to `Email`:
```python
preprocessed_text = Column(Text, nullable=True)  # The text sent to the LLM (after glossary context was added)
```

### 3.2 LLM Changes for Source Mapping

**Modified file**: `src/services/llm_parser.py`

> **Schema design**: The existing schemas use `"strict": True` with `"additionalProperties": false`. OpenAI's strict mode does NOT support `"type": ["string", "null"]` union syntax — it requires `"anyOf": [{"type": "string"}, {"type": "null"}]`. Rather than doubling the per-field properties (which would roughly double output tokens and cost), use a **separate `source_mappings` object** at the top level of each extraction response:

```python
# Instead of adding source_text to each field, add a sibling object:
SELLER_EXTRACTION_SCHEMA = {
    # ... existing schema ...
    "properties": {
        "listings": { ... },  # existing, unchanged
        "source_mappings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "snippet": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "listing_index": {"type": "integer"}  # which listing this maps to
                },
                "required": ["field", "snippet", "listing_index"],
                "additionalProperties": False,
            }
        }
    },
    "required": ["listings", "source_mappings"],
}
```

The system prompt is updated to instruct the LLM:
```
For each field you extract, also provide the original text snippet from the email
in the "source_mappings" array. Each entry should have the field name, the verbatim
snippet, and the index of the listing it belongs to.
```

> **Token cost**: This approach adds ~30-50% output tokens (one `source_mappings` array) rather than ~100% (duplicating every field). The `source_mappings` array is compact since many fields share nearby source text. Both `SELLER_EXTRACTION_SCHEMA` and `BUYER_EXTRACTION_SCHEMA` constants must be updated together with the prompt changes.

> **Phase ordering note**: Since Phase 1 modifies the system prompts (glossary injection) and Phase 3 modifies both prompts and JSON schemas, the schema changes should be designed during Phase 1 planning to avoid rework. The actual source_mapping implementation waits for Phase 3, but the schema structure should be forward-compatible.

The extraction functions will strip `source_mappings` from the LLM response and store them in the `source_mapping` column as JSON.

### 3.3 Parse Transparency API

**Modified file**: `src/routers/listings.py`

- `GET /api/listings/{id}` response now includes `source_mapping` and the source email's `body_text`
- No new endpoints needed — extend `ListingDetailResponse`

**Modified file**: `src/schemas.py`

```python
class FieldSourceMapping(BaseModel):
    field_name: str
    extracted_value: str | None
    source_text: str | None  # Original snippet from email

class ListingDetailResponse(ListingResponse):
    email: EmailResponse | None = None
    attachments: list[AttachmentResponse] = []
    source_mappings: list[FieldSourceMapping] = []  # NEW
```

### 3.4 Parse Transparency UI (Frontend)

**New file**: `frontend/src/components/ParseTransparency.tsx`

Side-by-side view:
- **Left panel**: Original email text with highlighted regions that map to extracted fields (color-coded)
- **Right panel**: Extracted fields, each showing:
  - Field name and value
  - The source snippet it came from (quoted, with highlight color matching the left panel)
  - Edit button (connects to Phase 2 feedback)

**Modified file**: `frontend/src/pages/ListingDetailPage.tsx`

- Add a "View Parse Details" expandable section or tab
- Renders the `ParseTransparency` component

**Modified file**: `frontend/src/components/ListingCard.tsx`

- Add a small "View source" link that navigates to the detail page with parse transparency visible

### 3.5 Click-Through Navigation

Already partially supported: `ListingDetailResponse` includes `email` with `body_text`. The parse transparency view completes this by showing the email text alongside the extraction.

From the listings list page, each listing card already links to `/listings/{id}`. The detail page will now show the source email and parse mapping.

### 3.6 Files Changed (Phase 3)

| File | Action |
|------|--------|
| `src/models.py` | Add `source_mapping` to Listing/BuyerRequest, `preprocessed_text` to Email |
| `src/services/llm_parser.py` | Extend extraction schemas to request source snippets |
| `src/services/email_ingestion.py` | Store source mappings and preprocessed text |
| `src/schemas.py` | Add `FieldSourceMapping`, extend `ListingDetailResponse` |
| `alembic/versions/xxx_add_transparency.py` | **New** — migration |
| `frontend/src/components/ParseTransparency.tsx` | **New** — side-by-side parse view |
| `frontend/src/pages/ListingDetailPage.tsx` | Add parse transparency section |
| `frontend/src/components/ListingCard.tsx` | Add "view source" link |

---

## Backward Compatibility

All changes are backward-compatible:

- **New DB columns** use `nullable=True` with defaults — existing rows unaffected
- **New API endpoints** are additive — no existing endpoints change their response shape in breaking ways
- **Extended responses** add new optional fields — existing frontend code ignores them until updated
- **LLM prompt changes** are additive — glossary section is appended, existing prompt behavior preserved
- **PATCH endpoints** are new — existing GET/POST endpoints unchanged
- The `glossary_section` parameter in LLM functions defaults to `""` so callers that don't pass it work unchanged

## Testability

### Unit Tests

| Test | What it covers |
|------|----------------|
| `tests/test_glossary.py` | CRUD operations on glossary entries, seed data loading, prompt section generation |
| `tests/test_glossary_prompt.py` | Verify glossary injection into system prompts produces valid prompts |
| `tests/test_feedback.py` | Field editing, correction recording, auto-learning trigger logic |
| `tests/test_reparse.py` | Re-parse flow: delete old data, re-extract, store new data |
| `tests/test_reclassify.py` | Reclassification flow: old data removed, new extraction runs |
| `tests/test_source_mapping.py` | Source mapping extraction and storage |
| `tests/test_abbreviation_detection.py` | Logic for detecting if a correction is an abbreviation expansion; false positive tests (location "TX"→"Dallas, TX" must NOT auto-learn, condition "NEW"→"New" must NOT auto-learn) |
| `tests/test_glossary_conflict.py` | Upsert behavior: seed vs auto-learned vs user priority; case-insensitive dedup; tombstone re-seed prevention |
| `tests/test_reparse_concurrency.py` | Re-parse while scan_lock is held returns 409; re-parse rate limiting returns 429 |

### Integration Tests

- **Glossary → LLM integration**: Mock OpenAI, verify that glossary entries appear in the prompt sent to the API
- **Feedback → Glossary integration**: Edit a field, verify glossary entry is auto-created
- **Re-parse integration**: Trigger re-parse, verify new glossary entries are used
- **End-to-end**: Process an email with abbreviations, verify glossary improves extraction on subsequent emails

### Manual Testing

- Process a test email containing "FRL" and verify it's expanded to "Freightliner"
- Edit a listing field and verify the correction appears in the glossary
- Re-parse an email and verify results improve
- View parse transparency and verify source snippets are correct

## Deployability

- **Migrations**: Each phase has its own Alembic migration. Migrations are forward-only and non-destructive.
- **Migration execution**: Migrations are **not** auto-run on app startup. The deploy process must run `alembic -c alembic/alembic.ini upgrade head` before starting the app. On Railway (current deploy target), add a start command or `Procfile` that runs migrations first:
  ```
  # Procfile
  web: alembic -c alembic/alembic.ini upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT
  ```
  Alternatively, add `alembic.command.upgrade(config, "head")` to the FastAPI lifespan in `src/main.py`.
- **Feature flags**: Not needed — each phase is independently deployable and backward-compatible.
- **Rollback**: Each migration can be reversed (columns dropped, tables dropped). No data migration required.
- **Zero downtime**: All changes are additive. Deploy backend first, then frontend.
- **SQLite compatibility**: All new columns/tables use SQLite-compatible types (String, Text, Integer, Boolean, DateTime).
- **SQLite migration safety**: Set `render_as_batch=True` in `alembic/env.py`'s `run_migrations_online()` context to future-proof migrations that modify existing columns/constraints (SQLite doesn't support `ALTER TABLE ... ADD CONSTRAINT`). This is not strictly needed for Phase 1 (new tables only) but prevents issues in Phases 2-3 and beyond.
- **DB size note**: The `preprocessed_text` column (Phase 3) on the `emails` table stores the full text sent to the LLM for every email, which will grow the SQLite DB. Not blocking, but worth monitoring.
- **No new env vars or pip dependencies required** — all features use existing deps (SQLAlchemy, FastAPI, OpenAI).

## Recommended: UX Teammate

The parse transparency feature (Phase 3) involves significant frontend design work — particularly the side-by-side view with color-coded source highlighting. I recommend spawning a **UX teammate** to design:
- The parse transparency layout (side-by-side vs. tabbed vs. overlay)
- The color-coding scheme for field-to-source mapping
- The inline editing UX for the feedback loop
- The glossary management page layout

## Summary of All New/Modified Files

### New Files (Backend)
- `src/services/glossary.py`
- `src/services/glossary_seed.py`
- `src/routers/glossary.py`
- `src/routers/feedback.py`
- 3 Alembic migrations
- Test files

### New Files (Frontend)
- `frontend/src/pages/GlossaryPage.tsx`
- `frontend/src/hooks/useGlossary.ts`
- `frontend/src/hooks/useFeedback.ts`
- `frontend/src/components/ParseTransparency.tsx`
- `frontend/src/components/EditableField.tsx`

### Modified Files (Backend)
- `src/models.py` — GlossaryEntry, FieldCorrection, new columns on Listing/BuyerRequest/Email; add `cascade="all, delete-orphan"` to Match relationships
- `src/schemas.py` — New schemas for glossary, feedback, source mapping
- `src/services/llm_parser.py` — Glossary injection, source mapping extraction
- `src/services/email_ingestion.py` — Pass glossary, store mappings, reparse/reclassify
- `src/routers/listings.py` — PATCH endpoint
- `src/routers/buyers.py` — PATCH endpoint
- `src/main.py` — Register new routers
- `src/database.py` — Enable SQLite FK enforcement (`PRAGMA foreign_keys=ON`)
- `alembic/env.py` — Add new model imports (`GlossaryEntry`, `FieldCorrection`); set `render_as_batch=True`

### Modified Files (Frontend)
- `frontend/src/App.tsx` — New routes
- `frontend/src/components/Layout.tsx` — New nav links
- `frontend/src/components/ListingDetail.tsx` — Inline editing, badges
- `frontend/src/pages/ListingDetailPage.tsx` — Parse transparency, re-parse, reclassify
- `frontend/src/components/ListingCard.tsx` — "View source" link
