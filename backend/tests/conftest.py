"""Test fixtures: test DB, mock OpenAI, sample data."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required env vars before importing app code
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from src.database import Base, get_db
from src.models import (
    Attachment,
    BuyerRequest,
    Email,
    Listing,
    Match,
    PriceBenchmark,
)


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _set_sqlite_pragmas)
    Base.metadata.create_all(bind=engine)
    # Create FTS5 table (not created by metadata.create_all since it's a virtual table)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS listings_fts USING fts5(
                make, model, engine_type, location, description, seller_name,
                content='listings', content_rowid='id'
            )
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS listings_ai AFTER INSERT ON listings BEGIN
                INSERT INTO listings_fts(rowid, make, model, engine_type, location, description, seller_name)
                VALUES (new.id, new.make, new.model, new.engine_type, new.location, new.description, new.seller_name);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS listings_au AFTER UPDATE ON listings BEGIN
                INSERT INTO listings_fts(listings_fts, rowid, make, model, engine_type, location, description, seller_name)
                VALUES ('delete', old.id, old.make, old.model, old.engine_type, old.location, old.description, old.seller_name);
                INSERT INTO listings_fts(rowid, make, model, engine_type, location, description, seller_name)
                VALUES (new.id, new.make, new.model, new.engine_type, new.location, new.description, new.seller_name);
            END
        """))
        conn.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def db(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_engine):
    from fastapi.testclient import TestClient

    Session = sessionmaker(bind=db_engine)

    def _get_test_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    from src.main import app
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_email(db):
    email = Email(
        id="test-msg-001",
        from_address="seller@test.com",
        from_name="Test Seller",
        subject="2022 Freightliner Cascadia",
        body_text="Selling a 2022 Freightliner Cascadia, 350k miles, $65,000",
        received_at=datetime(2026, 5, 1, 9, 0),
        classification="seller_listing",
    )
    db.add(email)
    db.commit()
    return email


@pytest.fixture
def sample_listing(db, sample_email):
    listing = Listing(
        email_id=sample_email.id,
        vehicle_type="truck",
        make="Freightliner",
        model="Cascadia",
        year=2022,
        mileage=350000,
        price=65000,
        location="Dallas, TX",
        engine_type="Detroit DD15",
        condition="Good",
        seller_name="Test Seller",
        seller_contact="seller@test.com",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@pytest.fixture
def sample_buyer(db):
    email = Email(
        id="test-msg-002",
        from_address="buyer@test.com",
        from_name="Test Buyer",
        subject="Looking for Cascadia",
        body_text="Need a 2020+ Cascadia, budget $70k",
        received_at=datetime(2026, 5, 2, 10, 0),
        classification="buyer_request",
    )
    db.add(email)
    db.flush()

    buyer = BuyerRequest(
        email_id=email.id,
        vehicle_type="truck",
        make="Freightliner",
        model="Cascadia",
        year_min=2020,
        year_max=2025,
        mileage_max=500000,
        price_min=40000,
        price_max=70000,
        buyer_name="Test Buyer",
        buyer_contact="buyer@test.com",
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@pytest.fixture
def sample_benchmark(db):
    benchmark = PriceBenchmark(
        vehicle_type="truck",
        make="Freightliner",
        model="Cascadia",
        year_min=2020,
        year_max=2024,
        mileage_min=200000,
        mileage_max=500000,
        benchmark_price=80000,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark
