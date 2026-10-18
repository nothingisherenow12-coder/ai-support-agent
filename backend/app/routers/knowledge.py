from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.knowledge import(
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeSource,
)
from app.services.ai_client import AIError, AIQuotaExceeded
from app.services.rag import generate_grounded_answer
from app.services.retrieval import search_similar_chunks
from google.genai.errors import APIError
from app.core.security import require_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(require_auth)],
)

QUOTA_DETAIL = (
    "The AI service has reached its request quota. "
    "Please try again later."
)
AI_FAILURE_DETAIL = "The AI service could not process the request."

@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
)
def query_knowledge(
    request: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
):
    try:
        results=search_similar_chunks(
            db=db,
            query=request.question,
            top_k=request.top_k,
        )
        rag_result=generate_grounded_answer(
            question=request.question,
            retrieved_chunks=results,
        )
        return KnowledgeQueryResponse(
            answer=rag_result.answer,
            sources=[
                KnowledgeSource(
                    document_id=source.document_id,
                    filename=source.filename,
                    chunk_id=source.chunk_id,
                    chunk_index=source.chunk_index,
                    distance=source.distance,
                )
                for source in rag_result.sources
            ],
            answerable=rag_result.answerable,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except AIQuotaExceeded as exc:
        logger.warning("AI quota exhausted while querying knowledge")
        raise HTTPException(
            status_code=503,
            detail=QUOTA_DETAIL,
            headers={"Retry-After": "3600"},
        ) from exc
    except AIError as exc:
        logger.error("AI request failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=AI_FAILURE_DETAIL,
        ) from exc
    except APIError as exc:
        logger.error("AI provider request failed (status=%s)", exc.code)
        if exc.code == 429:
            raise HTTPException(
                status_code=503,
                detail=QUOTA_DETAIL,
                headers={"Retry-After": "3600"},
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=AI_FAILURE_DETAIL,
        ) from exc



