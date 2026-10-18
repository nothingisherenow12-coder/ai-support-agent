from pydantic import BaseModel, Field
from datetime import datetime

class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)

class KnowledgeSource(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    chunk_index: int
    distance: float

class KnowledgeQueryResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSource]
    answerable: bool


class DocumentSummary(BaseModel):
    id: int
    filename: str
    created_at: datetime
    chunks_created: int
