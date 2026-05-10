"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "emails",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("from_address", sa.String(), nullable=True),
        sa.Column("from_name", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("classification", sa.String(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email_id", sa.String(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=True),
        sa.Column("make", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("engine_type", sa.String(), nullable=True),
        sa.Column("condition", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("seller_name", sa.String(), nullable=True),
        sa.Column("seller_contact", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_deal", sa.Boolean(), server_default="0"),
        sa.Column("deal_savings", sa.Numeric(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default="0"),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "buyer_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email_id", sa.String(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=True),
        sa.Column("make", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("year_min", sa.Integer(), nullable=True),
        sa.Column("year_max", sa.Integer(), nullable=True),
        sa.Column("mileage_max", sa.Integer(), nullable=True),
        sa.Column("price_min", sa.Numeric(), nullable=True),
        sa.Column("price_max", sa.Numeric(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("engine_type", sa.String(), nullable=True),
        sa.Column("buyer_name", sa.String(), nullable=True),
        sa.Column("buyer_contact", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default="0"),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "price_benchmarks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("vehicle_type", sa.String(), nullable=True),
        sa.Column("make", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("year_min", sa.Integer(), nullable=True),
        sa.Column("year_max", sa.Integer(), nullable=True),
        sa.Column("mileage_min", sa.Integer(), nullable=True),
        sa.Column("mileage_max", sa.Integer(), nullable=True),
        sa.Column("benchmark_price", sa.Numeric(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email_id", sa.String(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("is_inline", sa.Boolean(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("buyer_request_id", sa.Integer(), sa.ForeignKey("buyer_requests.id"), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("matched_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # FTS5 virtual table for full-text search on listings
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS listings_fts USING fts5(
            make, model, engine_type, location, description, seller_name,
            content='listings',
            content_rowid='id'
        )
    """)

    # Triggers to keep FTS index in sync
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS listings_ai AFTER INSERT ON listings BEGIN
            INSERT INTO listings_fts(rowid, make, model, engine_type, location, description, seller_name)
            VALUES (new.id, new.make, new.model, new.engine_type, new.location, new.description, new.seller_name);
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS listings_ad AFTER DELETE ON listings BEGIN
            INSERT INTO listings_fts(listings_fts, rowid, make, model, engine_type, location, description, seller_name)
            VALUES ('delete', old.id, old.make, old.model, old.engine_type, old.location, old.description, old.seller_name);
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS listings_au AFTER UPDATE ON listings BEGIN
            INSERT INTO listings_fts(listings_fts, rowid, make, model, engine_type, location, description, seller_name)
            VALUES ('delete', old.id, old.make, old.model, old.engine_type, old.location, old.description, old.seller_name);
            INSERT INTO listings_fts(rowid, make, model, engine_type, location, description, seller_name)
            VALUES (new.id, new.make, new.model, new.engine_type, new.location, new.description, new.seller_name);
        END
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS listings_au")
    op.execute("DROP TRIGGER IF EXISTS listings_ad")
    op.execute("DROP TRIGGER IF EXISTS listings_ai")
    op.execute("DROP TABLE IF EXISTS listings_fts")
    op.drop_table("matches")
    op.drop_table("attachments")
    op.drop_table("price_benchmarks")
    op.drop_table("buyer_requests")
    op.drop_table("listings")
    op.drop_table("emails")
