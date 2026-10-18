from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ActionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: Literal["create_ticket"]
    customer_id: int | None
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    requires_approval: Literal[True] = True

class ActionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    customer_id: int | None
    title: str
    description: str
    reason: str
    status: Literal["proposed", "approved", "rejected", "executed"]
    created_at: datetime
    updated_at: datetime
