"""Add feedback columns and field_corrections table

Revision ID: 004
Revises: 003
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # Add feedback columns to listings
    with op.batch_alter_table("listings") as batch_op:
        batch_op.add_column(sa.Column("user_edited", sa.Boolean(), server_default=sa.text("0")))
        batch_op.add_column(sa.Column("user_edited_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("original_extracted_data", sa.Text(), nullable=True))

    # Add feedback columns to buyer_requests
    with op.batch_alter_table("buyer_requests") as batch_op:
        batch_op.add_column(sa.Column("user_edited", sa.Boolean(), server_default=sa.text("0")))
        batch_op.add_column(sa.Column("user_edited_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("original_extracted_data", sa.Text(), nullable=True))

    # Add reclassify/reparse columns to emails
    with op.batch_alter_table("emails") as batch_op:
        batch_op.add_column(sa.Column("user_reclassified", sa.Boolean(), server_default=sa.text("0")))
        batch_op.add_column(sa.Column("original_classification", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("reprocessed_at", sa.DateTime(), nullable=True))

    # Create field_corrections table
    op.create_table(
        "field_corrections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("original_value", sa.String(), nullable=True),
        sa.Column("corrected_value", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("field_corrections")

    with op.batch_alter_table("emails") as batch_op:
        batch_op.drop_column("reprocessed_at")
        batch_op.drop_column("original_classification")
        batch_op.drop_column("user_reclassified")

    with op.batch_alter_table("buyer_requests") as batch_op:
        batch_op.drop_column("original_extracted_data")
        batch_op.drop_column("user_edited_at")
        batch_op.drop_column("user_edited")

    with op.batch_alter_table("listings") as batch_op:
        batch_op.drop_column("original_extracted_data")
        batch_op.drop_column("user_edited_at")
        batch_op.drop_column("user_edited")
