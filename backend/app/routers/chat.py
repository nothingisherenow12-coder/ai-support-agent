from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.schemas.orchestrator import OrchestratorResponse
from app.services.ai_client import AIError, AIQuotaExceeded
from app.services.orchestrator import handle_user_message
from google.genai.errors import APIError
from app.core.security import require_role
from app.core.clock import utcnow_naive
from app.models.chat_conversation import ChatConversation
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat_history import ConversationCreate, ConversationSummary, StoredChatMessage
from app.services.audit import record_event
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
    dependencies=[Depends(require_role("admin", "agent"))],
)


@router.post("/conversations", response_model=ConversationSummary, status_code=201)
def create_conversation(request: ConversationCreate, db: Session = Depends(get_db), user: User = Depends(require_role("admin", "agent"))):
    conversation = ChatConversation(user_id=user.id, title=request.title.strip()[:200] or "New conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    record_event(db, user, "chat.conversation_created", "chat_conversation", conversation.id)
    return conversation


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), user: User = Depends(require_role("admin", "agent"))):
    return db.execute(select(ChatConversation).where(ChatConversation.user_id == user.id).order_by(ChatConversation.updated_at.desc()).limit(limit)).scalars().all()


@router.get("/conversations/{conversation_id}/messages", response_model=list[StoredChatMessage])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("admin", "agent"))):
    conversation = db.execute(select(ChatConversation).where(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id)).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return db.execute(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.id)).scalars().all()


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("admin", "agent"))):
    conversation = db.execute(select(ChatConversation).where(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id)).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conversation)
    db.commit()
    record_event(db, user, "chat.conversation_deleted", "chat_conversation", conversation_id)
    return Response(status_code=204)

QUOTA_DETAIL = (
    "The AI service has reached its request quota. "
    "Please try again later."
)


def _ai_http_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail="The AI service could not process the request.",
    )


def _quota_http_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=QUOTA_DETAIL,
        headers={"Retry-After": "3600"},
    )



@router.post(
    "",
    response_model=OrchestratorResponse,
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "agent")),
):
    try:
        if request.conversation_id is not None:
            conversation = db.execute(select(ChatConversation).where(
                ChatConversation.id == request.conversation_id,
                ChatConversation.user_id == user.id,
            )).scalar_one_or_none()
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found.")
        else:
            conversation = ChatConversation(user_id=user.id, title=request.message.strip()[:200] or "New conversation")
            db.add(conversation)
            db.flush()

        result = OrchestratorResponse.model_validate(handle_user_message(
            db=db,
            message=request.message.strip(),
            context=[item.strip()[:1000] for item in request.context if item.strip()],
        ))
        if conversation.title == "New conversation":
            conversation.title = request.message.strip()[:200] or "New conversation"
        conversation.updated_at = utcnow_naive()
        db.add(ChatMessage(conversation_id=conversation.id, role="user", content=request.message.strip()))
        db.add(ChatMessage(conversation_id=conversation.id, role="assistant", content=result.answer, payload=result.model_dump(mode="json")))
        db.commit()
        record_event(db, user, "chat.message_processed", "chat_conversation", conversation.id, {"intent": result.intent})
        result.conversation_id = conversation.id
        return result

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except AIQuotaExceeded as exc:
        logger.warning("AI quota exhausted while handling chat request")
        raise _quota_http_error(exc) from exc

    except AIError as exc:
        logger.error("AI request failed (%s)", type(exc).__name__)
        raise _ai_http_error(exc) from exc

    except APIError as exc:
        logger.error("AI provider request failed (status=%s)", exc.code)
        if exc.code == 429:
            raise _quota_http_error(exc) from exc

        raise _ai_http_error(exc) from exc
