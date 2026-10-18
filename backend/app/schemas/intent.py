from typing import Literal
from pydantic import BaseModel, Field

class IntentClassification(BaseModel):
    intent: Literal["knowledge", "data", "action"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str