from pathlib import Path
import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session 
from app.models.document import Document 
from app.services.chunker import chunk_text
from app.services.document_service import save_document_chunks
from app.services.parser import extract_text_from_pdf

def ingest_pdf(
        db:Session,
        file_path:str,
        filename:str,
)-> Document:
    path=Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found:{file_path}")
    
    if path.suffix.lower() !=".pdf":
        raise ValueError("Only PDF files are supported.")
    
    text=extract_text_from_pdf(str(path))

    normalized_text = " ".join(text.split()).casefold()
    digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    existing = db.execute(
        select(Document).where(Document.content_sha256 == digest)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    if not text.strip():
        raise ValueError("PDF does not contain extractable text.")
    
    chunks=chunk_text(text)

    if not chunks:
        raise ValueError("PDF did not produce any chunks.")
    document=Document(
        filename=filename,
        content_sha256=digest,
        )
    try:
        db.add(document)
        db.flush()
        save_document_chunks(db=db, document_id=document.id, chunks=chunks)
        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        raise



