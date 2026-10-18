from datetime import datetime

from sqlalchemy import DateTime,ForeignKey,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.base import Base
from app.core.clock import utcnow_naive

class Ticket(Base):
    __tablename__="tickets"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    customer_id:Mapped[int]=mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )
    title:Mapped[str]=mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True, unique=True)
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )  
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False,
    )
    customer = relationship(
        "Customer",
        back_populates="tickets",
    )   
