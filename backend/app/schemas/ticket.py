from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class TicketResponse(BaseModel):
    id: int
    customer_id: int
    title: str
    description: str
    external_id: str | None = None
    priority: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved", "closed"] | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None

    @model_validator(mode="after")
    def require_update(self):
        if self.status is None and self.priority is None:
            raise ValueError("Provide a status or priority to update.")
        return self


class TicketPage(BaseModel):
    items: list[TicketResponse]
    total: int
    limit: int
    offset: int
