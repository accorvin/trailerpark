from datetime import datetime

from pydantic import BaseModel


# --- Listing schemas ---

class ListingBase(BaseModel):
    vehicle_type: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = None
    price: float | None = None
    location: str | None = None
    engine_type: str | None = None
    condition: str | None = None
    quantity: int | None = 1
    seller_name: str | None = None
    seller_contact: str | None = None
    description: str | None = None


class ListingResponse(ListingBase):
    id: int
    email_id: str
    is_deal: bool = False
    deal_savings: float | None = None
    is_archived: bool = False
    archived_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


class ListingDetailResponse(ListingResponse):
    email: "EmailResponse | None" = None
    attachments: list["AttachmentResponse"] = []

    model_config = {"from_attributes": True}


# --- Buyer request schemas ---

class BuyerRequestBase(BaseModel):
    vehicle_type: str | None = None
    make: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    mileage_max: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    location: str | None = None
    engine_type: str | None = None
    buyer_name: str | None = None
    buyer_contact: str | None = None
    description: str | None = None


class BuyerRequestResponse(BuyerRequestBase):
    id: int
    email_id: str
    is_archived: bool = False
    archived_at: datetime | None = None
    first_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


class BuyerDetailResponse(BuyerRequestResponse):
    matches: list["MatchResponse"] = []

    model_config = {"from_attributes": True}


# --- Price benchmark schemas ---

class BenchmarkBase(BaseModel):
    vehicle_type: str | None = None
    make: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    mileage_min: int | None = None
    mileage_max: int | None = None
    benchmark_price: float
    notes: str | None = None


class BenchmarkCreate(BenchmarkBase):
    pass


class BenchmarkUpdate(BaseModel):
    vehicle_type: str | None = None
    make: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    mileage_min: int | None = None
    mileage_max: int | None = None
    benchmark_price: float | None = None
    notes: str | None = None


class BenchmarkResponse(BenchmarkBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Email schemas ---

class EmailResponse(BaseModel):
    id: str
    from_address: str | None = None
    from_name: str | None = None
    subject: str | None = None
    body_text: str | None = None
    received_at: datetime | None = None
    classification: str | None = None
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Attachment schemas ---

class AttachmentResponse(BaseModel):
    id: int
    email_id: str
    filename: str
    content_type: str | None = None
    file_size: int | None = None
    is_inline: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Match schemas ---

class MatchResponse(BaseModel):
    id: int
    buyer_request_id: int
    listing_id: int
    score: float
    matched_at: datetime | None = None
    buyer_request: BuyerRequestResponse | None = None
    listing: ListingResponse | None = None

    model_config = {"from_attributes": True}


# --- Stats schemas ---

class StatsResponse(BaseModel):
    active_listings: int = 0
    deals_count: int = 0
    buyers_count: int = 0
    matches_count: int = 0
    attachment_storage_bytes: int = 0


# --- Paginated response ---

class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    pages: int = 0
