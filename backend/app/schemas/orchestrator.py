from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.action import ActionProposal

class OrchestratorResponse(BaseModel):
    intent: Literal["knowledge", "data", "action"]
    answer: str
    data: Any | None = None
    sources: list[dict] = Field(default_factory=list)
    requires_approval: bool = False
    action: ActionProposal | None = None
    action_id: int | None = None
    conversation_id: int | None = None
