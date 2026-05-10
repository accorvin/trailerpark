"""Add source_mapping and preprocessed_text columns

Revision ID: 005
Revises: 004
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch_op:
        batch_op.add_column(sa.Column("source_mapping", sa.Text(), nullable=True))

    with op.batch_alter_table("buyer_requests") as batch_op:
        batch_op.add_column(sa.Column("source_mapping", sa.Text(), nullable=True))

    with op.batch_alter_table("emails") as batch_op:
        batch_op.add_column(sa.Column("preprocessed_text", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("emails") as batch_op:
        batch_op.drop_column("preprocessed_text")

    with op.batch_alter_table("buyer_requests") as batch_op:
        batch_op.drop_column("source_mapping")

    with op.batch_alter_table("listings") as batch_op:
        batch_op.drop_column("source_mapping")
