> **NOTE: This is the original requirements document. The approved implementation plan is in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), which supersedes this document.**

# TrailerPark — Project Plan

## Overview

TrailerPark is a deal-matching app for a commercial truck and trailer broker. It consumes emails from a single Outlook inbox, extracts structured listing data (items for sale and buyer requests), tracks inventory over time, and surfaces potential deals via a web dashboard.

**User**: Single user (broker at truthtruckgroup.com)
**Hosting**: Local (office computer only)

---

## Problem Statement

The broker receives 40-100 emails/day from sellers/dealers (inventory listings) and buyers (purchase requests). These emails are unstructured — free-form text, photos, Excel attachments, PDFs — and come from many different senders with no standard format. Today there is no system to organize, track, or match this data. Good deals are missed or spotted too late.

---

## Core Features

### 1. Email Ingestion
- Connect to the broker's Outlook/M365 inbox via Microsoft Graph API
- Poll for new emails periodically (every ~30 minutes)
- Filter out non-truck-related emails (personal, spam, newsletters, etc.) using LLM classification
- Extract email body text, and download attachments (PDFs, Excel, images)

### 2. Email Parsing & Data Extraction
- Use an LLM (OpenAI or Anthropic) to parse unstructured email content into structured data
- Extract: make, model, year, mileage, price, location, engine type, condition, quantity, seller/buyer info
- Classify each email as: **seller listing**, **buyer request**, or **irrelevant**
- For text-based emails: parse directly with LLM
- For PDF/Excel attachments: extract text first, then parse with LLM
- For image-only emails (screenshots with no text): use vision model as fallback
- Vehicle categories: Class 8 semi trucks, trailers, medium duty trucks

### 3. Inventory Tracking
- Store all extracted listings in a database with timestamps
- Track listing age (first seen date)
- Auto-archive listings older than 20 days (assumed no longer active)
- Archived listings remain searchable but hidden from the main feed

### 4. Pricing & Deal Detection
- Build an internal pricing model from accumulated listing data over time
- Group by similar specs (make, model, year range, mileage range, engine type)
- Calculate average/median asking prices per spec group
- Allow manual benchmark prices set by the broker for common configurations
- Flag deals priced $10,000-$20,000+ below the average for similarly-spec'd equipment

### 5. Buyer-Seller Matching
- Match buyer requests against active seller listings by specs (make, model, year, price range, etc.)
- Surface matched pairs: "Buyer X wants [specs] — Seller Y has [listing]"
- Rank matches by relevance/closeness of spec match

### 6. Web Dashboard
- **Deals feed**: Listings flagged as below-market, sorted by deal quality
- **All listings**: Browsable/filterable feed of all active seller listings
- **Buyer requests**: Active buyer requests with matched listings shown inline
- **Matched pairs**: Dedicated view showing buyer-seller matches
- **Listing detail**: Full details for any listing, including original email content and attachments
- **Filters**: Make, model, year range, price range, location, vehicle type, listing age
- **Search**: Free-text search across all listings
- **Manual benchmarks**: Simple UI for the broker to set/edit market price benchmarks
- **Archive**: View archived (expired) listings separately
- Designed for checking ~3x/day (morning, noon, end of day)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web Dashboard                      │
│               (React or plain HTML/JS)               │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│                  API Server                          │
│               (Python / FastAPI)                     │
│                                                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Email       │ │ Parser       │ │ Deal         │  │
│  │ Ingestion   │ │ Service      │ │ Detection    │  │
│  │ (Graph API) │ │ (LLM)       │ │ Engine       │  │
│  └─────────────┘ └──────────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌──────────────┐                    │
│  │ Matcher     │ │ Archiver     │                    │
│  │ Service     │ │ (cron/task)  │                    │
│  └─────────────┘ └──────────────┘                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   SQLite Database                     │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| Database | SQLite (single user, local) |
| ORM | SQLAlchemy or raw SQL |
| Email access | Microsoft Graph API (`msgraph-sdk` + `azure-identity`) |
| LLM (text parsing) | OpenAI API or Anthropic API |
| LLM (image fallback) | OpenAI GPT-4o vision or Anthropic Claude vision |
| PDF extraction | `pymupdf` or `pdfplumber` |
| Excel extraction | `openpyxl` |
| Frontend | React (Vite) or plain HTML/JS + TailwindCSS |
| Task scheduling | APScheduler (in-process) or cron |
| Package manager | uv |

---

## Data Model

### emails
| Column | Type | Description |
|---|---|---|
| id | TEXT (PK) | Graph API message ID |
| from_address | TEXT | Sender email |
| from_name | TEXT | Sender display name |
| subject | TEXT | Email subject |
| received_at | DATETIME | When the email was received |
| body_text | TEXT | Plain text body |
| classification | TEXT | "seller_listing", "buyer_request", "irrelevant" |
| processed_at | DATETIME | When we parsed it |
| raw_json | TEXT | Full Graph API response (for debugging) |

### listings (seller inventory)
| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-increment |
| email_id | TEXT (FK) | Source email |
| vehicle_type | TEXT | "semi_truck", "trailer", "medium_duty" |
| make | TEXT | e.g., "Freightliner", "Great Dane" |
| model | TEXT | e.g., "Cascadia", "53ft Reefer" |
| year | INTEGER | Model year |
| mileage | INTEGER | Odometer reading (nullable for trailers) |
| price | DECIMAL | Asking price |
| location | TEXT | City/state |
| engine_type | TEXT | e.g., "Cummins X15", "Detroit DD15" |
| condition | TEXT | e.g., "excellent", "good", "fair" |
| quantity | INTEGER | Number available (default 1) |
| description | TEXT | Free-text details from the email |
| first_seen_at | DATETIME | When first ingested |
| last_seen_at | DATETIME | Most recent mention |
| is_archived | BOOLEAN | True if older than 20 days |
| archived_at | DATETIME | When archived |
| is_deal | BOOLEAN | Flagged as below-market |
| deal_savings | DECIMAL | Estimated $ below market |
| seller_name | TEXT | Seller/dealer name |
| seller_contact | TEXT | Seller phone/email |

### buyer_requests
| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-increment |
| email_id | TEXT (FK) | Source email |
| vehicle_type | TEXT | What they're looking for |
| make | TEXT | Preferred make(s) |
| model | TEXT | Preferred model(s) |
| year_min | INTEGER | Minimum year |
| year_max | INTEGER | Maximum year |
| mileage_max | INTEGER | Max acceptable mileage |
| price_min | DECIMAL | Budget floor |
| price_max | DECIMAL | Budget ceiling |
| location | TEXT | Preferred location/region |
| engine_type | TEXT | Preferred engine |
| description | TEXT | Free-text details |
| first_seen_at | DATETIME | When first ingested |
| is_archived | BOOLEAN | Archived after 20 days |
| buyer_name | TEXT | Buyer name |
| buyer_contact | TEXT | Buyer phone/email |

### price_benchmarks (manual)
| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-increment |
| vehicle_type | TEXT | Category |
| make | TEXT | Make |
| model | TEXT | Model (nullable for broad benchmarks) |
| year_min | INTEGER | Year range start |
| year_max | INTEGER | Year range end |
| mileage_min | INTEGER | Mileage range start |
| mileage_max | INTEGER | Mileage range end |
| market_price | DECIMAL | Expected market price |
| updated_at | DATETIME | Last updated |

### attachments
| Column | Type | Description |
|---|---|---|
| id | INTEGER (PK) | Auto-increment |
| email_id | TEXT (FK) | Source email |
| filename | TEXT | Original filename |
| content_type | TEXT | MIME type |
| file_path | TEXT | Local storage path |
| extracted_text | TEXT | Text extracted from the attachment |

---

## Microsoft Graph API Setup

### Prerequisites
- Admin access to the M365 tenant (truthtruckgroup.com)
- Access to Microsoft Entra admin center (entra.microsoft.com)

### Steps
1. Go to entra.microsoft.com > Applications > App registrations > New registration
2. Name: "TrailerPark" / Single tenant
3. Note the **Application (client) ID** and **Directory (tenant) ID**
4. API permissions > Add > Microsoft Graph > Application permissions > `Mail.Read`
5. Grant admin consent
6. Certificates & secrets > New client secret > Save the value
7. (Optional but recommended) Create an Application Access Policy to restrict to one mailbox:
   ```powershell
   New-ApplicationAccessPolicy -AppId "<AppId>" \
     -PolicyScopeGroupId "<SecurityGroupEmail>" \
     -AccessRight RestrictAccess
   ```

### Config needed in .env
```
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
GRAPH_USER_EMAIL=user@truthtruckgroup.com
```

---

## Pricing / Deal Detection Logic

### Phase 1: Manual Benchmarks
- Broker sets market price benchmarks via the dashboard for common spec combos
- Any listing priced $10k-$20k+ below the benchmark is flagged as a deal

### Phase 2: Accumulated Data Model
- As listings accumulate, compute rolling averages per spec group
- Spec group = vehicle_type + make + model + year_range + mileage_range
- Need minimum 5 data points in a group before auto-computing benchmarks
- Manual benchmarks override auto-computed ones when both exist
- Deal threshold: configurable, default $10,000 below average

---

## Estimated Costs

| Item | Monthly Cost |
|---|---|
| Microsoft Graph API | Free (included with M365) |
| LLM text parsing (40-100 emails/day) | ~$5-15/month |
| LLM image vision (fallback only) | ~$5-10/month |
| Hosting | Free (runs locally) |
| Database | Free (SQLite) |
| **Total** | **~$10-25/month** |

---

## Implementation Phases

### Phase 1: Foundation
- Project scaffolding (Python, FastAPI, SQLite, uv)
- Database schema and migrations
- Config management (.env)

### Phase 2: Email Ingestion
- Microsoft Graph API integration
- Email polling (every 30 min)
- Attachment downloading and text extraction (PDF, Excel)
- Email relevance classification (LLM)

### Phase 3: Parsing Engine
- LLM prompt engineering for structured data extraction
- Text email parsing
- Attachment content parsing
- Image fallback parsing (vision model)
- Store parsed data to database

### Phase 4: Deal Detection & Matching
- Manual benchmark CRUD
- Auto-computed pricing from accumulated data
- Deal flagging logic
- Buyer-seller matching algorithm

### Phase 5: Web Dashboard
- API endpoints for all data views
- Frontend: deals feed, listings, buyer requests, matched pairs
- Filters, search, listing detail view
- Manual benchmark management UI
- Archive view

### Phase 6: Polish
- Auto-archiving (20-day expiry)
- De-duplication (same truck listed by multiple sellers)
- Error handling and logging
- Startup script / process management
