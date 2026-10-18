from typing import Annotated
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000,
        description="The user's support request or question.",
    )
    context: list[Annotated[str, Field(max_length=1000)]] = Field(default_factory=list, max_length=6)
    conversation_id: int | None = Field(default=None, ge=1)
