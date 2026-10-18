from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket import Ticket

def get_ticket(
    db: Session,
    ticket_id: int,
) -> dict | None:
    statement = select(Ticket).where(
        Ticket.id == ticket_id
    )

    ticket = db.execute(statement).scalar_one_or_none()

    if ticket is None:
        return None

    return {
        "id": ticket.id,
        "customer_id": ticket.customer_id,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }

def list_open_tickets(
    db: Session,
) -> list[dict]:
    statement = (
        select(Ticket)
        .where(Ticket.status == "open")
        .order_by(Ticket.created_at.desc())
    )

    tickets = db.execute(statement).scalars().all()

    return [
        {
            "id": ticket.id,
            "customer_id": ticket.customer_id,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
        }
        for ticket in tickets
    ]