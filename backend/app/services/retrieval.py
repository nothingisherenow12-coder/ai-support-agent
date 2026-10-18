from dataclasses import dataclass
import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding import generate_query_embedding

@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    distance: float

def search_similar_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_embedding = generate_query_embedding(query)

    # When a user names a document type, keep similarly named files from
    # competing with it. This matters in workspaces with many unrelated PDFs.
    normalized_query = query.casefold()
    resume_query = bool(
        re.search(r"\b(resume|resumes|cv|cvs|curriculum vitae)\b", normalized_query)
    )

    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    )
    statement = select(DocumentChunk, distance.label("distance")).join(
        Document, Document.id == DocumentChunk.document_id
    ).where(
        DocumentChunk.embedding.is_not(None)
    )
    if resume_query:
        statement = statement.where(
            or_(
                Document.filename.ilike("%resume%"),
                Document.filename.ilike("%cv%"),
            )
        )
    statement = (
        statement
        .order_by(distance, Document.created_at.desc(), DocumentChunk.chunk_index)
        # Repeated uploads otherwise fill every result slot with identical
        # passages before we have a chance to remove those duplicates.
        .limit(max(top_k * 10, top_k + 250))
    )
    rows = db.execute(statement).all()

    results: list[RetrievedChunk] = []
    seen_content: set[str] = set()
    for chunk, distance_value in rows:
        fingerprint = " ".join(chunk.content.casefold().split())
        if fingerprint in seen_content:
            continue
        seen_content.add(fingerprint)
        results.append(RetrievedChunk(chunk=chunk, distance=float(distance_value)))
        if len(results) == top_k:
            break
    return results
