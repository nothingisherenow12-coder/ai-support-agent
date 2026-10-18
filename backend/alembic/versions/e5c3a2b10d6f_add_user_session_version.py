"""Add a version counter to revoke sessions after password changes.

Revision ID: e5c3a2b10d6f
Revises: d19f7c42a8e1
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5c3a2b10d6f"
down_revision: Union[str, Sequence[str], None] = "d19f7c42a8e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "session_version")
