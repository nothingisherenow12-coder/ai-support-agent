from typing import Literal
from pydantic import BaseModel

class ToolCall(BaseModel):
    tool_name: Literal[
        "get_customer",
        "get_customer_tickets",
        "get_ticket",
        "list_open_tickets",
    ]
    customer_id: int | None
    ticket_id: int | None
    reason: str