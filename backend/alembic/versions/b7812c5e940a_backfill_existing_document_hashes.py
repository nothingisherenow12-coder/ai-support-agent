"""Backfill fingerprints for documents already present at the prior head.

Revision ID: b7812c5e940a
Revises: a4c81d0f62b1
Create Date: 2026-10-16
"""
import hashlib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7812c5e940a"
down_revision: Union[str, Sequence[str], None] = "a4c81d0f62b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id FROM documents WHERE content_sha256 IS NULL ORDER BY id")
    ).scalars().all()
    existing = set(connection.execute(
        sa.text("SELECT content_sha256 FROM documents WHERE content_sha256 IS NOT NULL")
    ).scalars().all())
    for document_id in rows:
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
        # Older repeated uploads remain available for manual cleanup. Only one
        # gets the unique fingerprint so it can prevent future duplicates.
        if digest in existing:
            continue
        connection.execute(
            sa.text("UPDATE documents SET content_sha256 = :digest WHERE id = :id"),
            {"digest": digest, "id": document_id},
        )
        existing.add(digest)


def downgrade() -> None:
    # Keeping hashes is safe; the previous schema and ingestion code ignore them.
    pass
