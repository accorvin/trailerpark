"""Add gmail_sync_state table

Revision ID: 002
Revises: 001
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gmail_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("last_history_id", sa.String(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_sync_status", sa.String(), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table("gmail_sync_state")
