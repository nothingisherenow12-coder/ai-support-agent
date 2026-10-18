"""Add an optional unique source ID for idempotent ticket imports.

Revision ID: d19f7c42a8e1
Revises: c4af9b17e2d0
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d19f7c42a8e1"
down_revision: Union[str, Sequence[str], None] = "c4af9b17e2d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("external_id", sa.String(length=128), nullable=True))
    op.create_index("ix_tickets_external_id", "tickets", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tickets_external_id", table_name="tickets")
    op.drop_column("tickets", "external_id")
