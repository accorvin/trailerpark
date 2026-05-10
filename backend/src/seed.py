"""Seed script for dev/testing. Creates sample listings, buyers, and benchmarks."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import SessionLocal, engine
from src.models import Base, Email, Listing, BuyerRequest, PriceBenchmark


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Sample emails
        emails_data = [
            Email(
                id="2026-05/2026-05-01T09-00-00",
                from_address="seller1@trucks.com",
                from_name="Big Rig Sales",
                subject="2022 Freightliner Cascadia - Great Price!",
                body_text="We have a 2022 Freightliner Cascadia with 350k miles. Detroit DD15 engine. Located in Dallas, TX. Asking $65,000.",
                received_at=datetime.now() - timedelta(days=3),
                classification="seller_listing",
            ),
            Email(
                id="2026-05/2026-05-02T10-30-00",
                from_address="seller2@transport.com",
                from_name="Fleet Liquidators",
                subject="Multiple Units Available - Peterbilt 579",
                body_text="Selling 5 units of 2021 Peterbilt 579. Cummins X15 engines. 400k-500k miles each. Priced from $55,000-$62,000. Located in Houston, TX.",
                received_at=datetime.now() - timedelta(days=2),
                classification="seller_listing",
            ),
            Email(
                id="2026-05/2026-05-03T14-00-00",
                from_address="buyer1@logistics.com",
                from_name="Smith Logistics",
                subject="Looking for Cascadias",
                body_text="We need 2020+ Freightliner Cascadias, under 500k miles, budget up to $70,000. Prefer Dallas area.",
                received_at=datetime.now() - timedelta(days=1),
                classification="buyer_request",
            ),
            Email(
                id="2026-05/2026-05-04T08-15-00",
                from_address="seller3@deals.com",
                from_name="Truck Depot",
                subject="DEAL: 2023 Kenworth T680 Low Miles",
                body_text="2023 Kenworth T680, only 180k miles. Paccar MX-13. Excellent condition. Phoenix, AZ. Only $72,000!",
                received_at=datetime.now() - timedelta(hours=12),
                classification="seller_listing",
            ),
            Email(
                id="2026-05/2026-05-04T09-00-00",
                from_address="newsletter@industry.com",
                from_name="Trucking News Weekly",
                subject="Weekly Industry Update",
                body_text="This week in trucking...",
                received_at=datetime.now() - timedelta(hours=10),
                classification="irrelevant",
            ),
        ]

        for email in emails_data:
            existing = db.get(Email, email.id)
            if not existing:
                db.add(email)

        db.flush()

        # Sample listings
        listings_data = [
            Listing(
                email_id="2026-05/2026-05-01T09-00-00",
                vehicle_type="truck",
                make="Freightliner",
                model="Cascadia",
                year=2022,
                mileage=350000,
                price=65000,
                location="Dallas, TX",
                engine_type="Detroit DD15",
                condition="Good",
                quantity=1,
                seller_name="Big Rig Sales",
                seller_contact="seller1@trucks.com",
                description="2022 Freightliner Cascadia, 350k miles, Detroit DD15 engine.",
                is_deal=True,
                deal_savings=15000,
            ),
            Listing(
                email_id="2026-05/2026-05-02T10-30-00",
                vehicle_type="truck",
                make="Peterbilt",
                model="579",
                year=2021,
                mileage=400000,
                price=55000,
                location="Houston, TX",
                engine_type="Cummins X15",
                condition="Good",
                quantity=5,
                seller_name="Fleet Liquidators",
                seller_contact="seller2@transport.com",
                description="2021 Peterbilt 579, Cummins X15, 400k miles.",
            ),
            Listing(
                email_id="2026-05/2026-05-02T10-30-00",
                vehicle_type="truck",
                make="Peterbilt",
                model="579",
                year=2021,
                mileage=500000,
                price=62000,
                location="Houston, TX",
                engine_type="Cummins X15",
                condition="Fair",
                quantity=1,
                seller_name="Fleet Liquidators",
                seller_contact="seller2@transport.com",
                description="2021 Peterbilt 579, Cummins X15, 500k miles.",
            ),
            Listing(
                email_id="2026-05/2026-05-04T08-15-00",
                vehicle_type="truck",
                make="Kenworth",
                model="T680",
                year=2023,
                mileage=180000,
                price=72000,
                location="Phoenix, AZ",
                engine_type="Paccar MX-13",
                condition="Excellent",
                quantity=1,
                seller_name="Truck Depot",
                seller_contact="seller3@deals.com",
                description="2023 Kenworth T680, 180k miles, Paccar MX-13. Excellent condition.",
                is_deal=True,
                deal_savings=23000,
            ),
        ]

        for listing in listings_data:
            db.add(listing)

        # Sample buyer requests
        buyer_data = [
            BuyerRequest(
                email_id="2026-05/2026-05-03T14-00-00",
                vehicle_type="truck",
                make="Freightliner",
                model="Cascadia",
                year_min=2020,
                year_max=2025,
                mileage_max=500000,
                price_min=40000,
                price_max=70000,
                location="Dallas, TX",
                buyer_name="Smith Logistics",
                buyer_contact="buyer1@logistics.com",
                description="Looking for 2020+ Cascadias, under 500k miles.",
            ),
        ]

        for buyer in buyer_data:
            db.add(buyer)

        # Sample benchmarks
        benchmarks_data = [
            PriceBenchmark(
                vehicle_type="truck",
                make="Freightliner",
                model="Cascadia",
                year_min=2020,
                year_max=2024,
                mileage_min=200000,
                mileage_max=500000,
                benchmark_price=80000,
                notes="Market average for mid-mileage Cascadias",
            ),
            PriceBenchmark(
                vehicle_type="truck",
                make="Kenworth",
                model="T680",
                year_min=2022,
                year_max=2025,
                benchmark_price=95000,
                notes="Premium model, typically higher pricing",
            ),
        ]

        for bench in benchmarks_data:
            db.add(bench)

        db.commit()
        print("Seed data created successfully!")
        print(f"  - {len(emails_data)} emails")
        print(f"  - {len(listings_data)} listings")
        print(f"  - {len(buyer_data)} buyer requests")
        print(f"  - {len(benchmarks_data)} price benchmarks")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
