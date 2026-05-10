from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True)  # relative folder path e.g. "2026-05/2026-05-09T08-30-00"
    from_address = Column(String, nullable=True)
    from_name = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True)
    classification = Column(String, nullable=True)  # seller_listing, buyer_request, irrelevant, parse_error
    raw_json = Column(Text, nullable=True)
    processed_at = Column(DateTime, server_default=func.now())

    listings = relationship("Listing", back_populates="email")
    buyer_requests = relationship("BuyerRequest", back_populates="email")
    attachments = relationship("Attachment", back_populates="email")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    vehicle_type = Column(String, nullable=True)  # truck, trailer, etc.
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    mileage = Column(Integer, nullable=True)
    price = Column(Numeric, nullable=True)
    location = Column(String, nullable=True)
    engine_type = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True, default=1)
    seller_name = Column(String, nullable=True)
    seller_contact = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_deal = Column(Boolean, default=False)
    deal_savings = Column(Numeric, nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, server_default=func.now())
    last_seen_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    email = relationship("Email", back_populates="listings")
    matches = relationship("Match", back_populates="listing")


class BuyerRequest(Base):
    __tablename__ = "buyer_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    vehicle_type = Column(String, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year_min = Column(Integer, nullable=True)
    year_max = Column(Integer, nullable=True)
    mileage_max = Column(Integer, nullable=True)
    price_min = Column(Numeric, nullable=True)
    price_max = Column(Numeric, nullable=True)
    location = Column(String, nullable=True)
    engine_type = Column(String, nullable=True)
    buyer_name = Column(String, nullable=True)
    buyer_contact = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, server_default=func.now())

    email = relationship("Email", back_populates="buyer_requests")
    matches = relationship("Match", back_populates="buyer_request")


class PriceBenchmark(Base):
    __tablename__ = "price_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_type = Column(String, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year_min = Column(Integer, nullable=True)
    year_max = Column(Integer, nullable=True)
    mileage_min = Column(Integer, nullable=True)
    mileage_max = Column(Integer, nullable=True)
    benchmark_price = Column(Numeric, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)  # relative to ATTACHMENT_DIR
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    is_inline = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    email = relationship("Email", back_populates="attachments")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_request_id = Column(Integer, ForeignKey("buyer_requests.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    score = Column(Float, nullable=False)
    matched_at = Column(DateTime, server_default=func.now())

    buyer_request = relationship("BuyerRequest", back_populates="matches")
    listing = relationship("Listing", back_populates="matches")
