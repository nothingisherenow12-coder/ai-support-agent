from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.ticket import Ticket

def get_customer(
    db: Session,
    customer_id: int,
) -> dict | None:
    statement = select(Customer).where(
        Customer.id == customer_id
    )
    customer = db.execute(statement).scalar_one_or_none()

    if customer is None:
        return None

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "company": customer.company,
        "created_at": customer.created_at.isoformat(),
    }
def get_customer_tickets(
    db: Session,
    customer_id: int,
) -> list[dict]:
    statement = (
        select(Ticket)
        .where(Ticket.customer_id == customer_id)
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