from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.base import Base
from app.core.clock import utcnow_naive

class Document(Base):
    __tablename__="documents"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    filename: Mapped[str]=mapped_column(
        String(255),
        nullable=False,
    )
    content_sha256: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False,
    )

    chunks=relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all,delete-orphan",
    )
