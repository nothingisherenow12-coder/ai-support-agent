from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime,ForeignKey,Integer,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base
from app.core.clock import utcnow_naive

class DocumentChunk(Base):
    __tablename__="document_chunks"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    document_id:Mapped[int]=mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )
    chunk_index:Mapped[int]=mapped_column(
        Integer,
        nullable=False,
    )
    content:Mapped[str]=mapped_column(
        Text,
        nullable=False,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False,
    )
    
    document = relationship(
    "Document",
    back_populates="chunks",
    )

   

