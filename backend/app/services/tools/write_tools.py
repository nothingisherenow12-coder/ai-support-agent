from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.ticket import Ticket

def create_ticket(
    db: Session,
    customer_id: int,
    title: str,
    description: str,
    priority: str = "medium",
) -> dict:
    """Create a ticket without committing.

    The caller owns the transaction commit so that ticket creation can
    share an atomic transaction with related state changes (e.g. marking
    an approved action as executed). Callers that use this tool directly
    must commit (or roll back) the session themselves.
    """
    customer = db.execute(
        select(Customer).where(Customer.id == customer_id)
    ).scalar_one_or_none()

    if customer is None:
        raise ValueError(f"Customer {customer_id} does not exist.")

    ticket = Ticket(
        customer_id=customer_id,
        title=title,
        description=description,
        priority=priority,
        status="open",
    )

    db.add(ticket)
    db.flush()
    db.refresh(ticket)

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