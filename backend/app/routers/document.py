from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.db.database import get_db
from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse
from app.services.ingestion import ingest_pdf
from app.core.security import require_auth, require_role
from app.models.user import User
from app.services.audit import record_event
from app.schemas.knowledge import DocumentSummary

router=APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],
    dependencies=[Depends(require_auth)],
)
@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
)
def upload_document(
    file:UploadFile=File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("admin", "agent")),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )
    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )
    temp_path=None
    max_bytes = settings.max_upload_bytes

    try:
        with NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            
            temp_path=temp_file.name

            received = 0
            while chunk:=file.file.read(1024*1024):
                received += len(chunk)
                if received > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"PDF is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.",
                    )
                temp_file.write(chunk)

        with open(temp_path, "rb") as uploaded_pdf:
            if uploaded_pdf.read(5) != b"%PDF-":
                raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

        document=ingest_pdf(
            db=db,
            file_path=temp_path,
            filename=file.filename,
        )        

        chunks_created=len(document.chunks)
        record_event(db, actor, "document.uploaded", "document", document.id, {"filename": document.filename})
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            chunks_created=chunks_created,
        )
    
    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    
    except Exception as exc:
        db.rollback()
        
        raise HTTPException(
            status_code=500,
            detail="Failed to ingest the PDF.",
        ) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        
        file.file.close()    


@router.get("", response_model=list[DocumentSummary])
def list_documents(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    documents = db.execute(select(Document).options(selectinload(Document.chunks)).order_by(Document.created_at.desc()).limit(limit)).scalars().all()
    return [DocumentSummary(id=d.id, filename=d.filename, created_at=d.created_at, chunks_created=len(d.chunks)) for d in documents]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db), actor: User = Depends(require_role("admin", "agent"))) -> Response:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    filename = document.filename
    db.delete(document)
    db.commit()
    record_event(db, actor, "document.deleted", "document", document_id, {"filename": filename})
    return Response(status_code=204)



