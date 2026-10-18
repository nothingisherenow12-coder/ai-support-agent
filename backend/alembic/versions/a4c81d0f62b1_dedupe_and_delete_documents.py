"""Add a content fingerprint for duplicate PDF prevention.

Revision ID: a4c81d0f62b1
Revises: 336ca9a57d21
Create Date: 2026-10-16
"""
from typing import Sequence, Union

import hashlib

from alembic import op
import sqlalchemy as sa

revision: str = "a4c81d0f62b1"
down_revision: Union[str, Sequence[str], None] = "336ca9a57d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("content_sha256", sa.String(length=64), nullable=True))
    connection = op.get_bind()
    document_ids = connection.execute(sa.text("SELECT id FROM documents ORDER BY id")).scalars()
    seen: set[str] = set()
    for document_id in document_ids:
        chunks = connection.execute(
            sa.text("SELECT content FROM document_chunks WHERE document_id = :id ORDER BY chunk_index"),
            {"id": document_id},
        ).scalars().all()
        if not chunks:
            continue
        reconstructed = chunks[0]
        for chunk in chunks[1:]:
            overlap = min(200, len(reconstructed), len(chunk))
            while overlap >= 20 and reconstructed[-overlap:] != chunk[:overlap]:
                overlap -= 1
            reconstructed += chunk[overlap:]
        normalized = " ".join(reconstructed.split()).casefold()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        # Keep one document as the canonical match; duplicate legacy uploads
        # remain deletable and are not allowed to block migration.
        if digest in seen:
            continue
        seen.add(digest)
        connection.execute(
            sa.text("UPDATE documents SET content_sha256 = :digest WHERE id = :id"),
            {"digest": digest, "id": document_id},
        )
    op.create_unique_constraint("uq_documents_content_sha256", "documents", ["content_sha256"])


def downgrade() -> None:
    op.drop_constraint("uq_documents_content_sha256", "documents", type_="unique")
    op.drop_column("documents", "content_sha256")
