"""Idempotently add 100 synthetic customers and 300 demo support tickets."""
from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.customer import Customer
from app.models.ticket import Ticket


def seed_demo_scale() -> None:
    db = SessionLocal()
    created_customers = 0
    created_tickets = 0
    scenarios = [
        ("Account access question", "Demo scenario: the customer needs help signing in.", "high", "open"),
        ("Billing clarification", "Demo scenario: the customer has a question about an invoice.", "medium", "in_progress"),
        ("Profile update request", "Demo scenario: the customer needs to update account details.", "low", "resolved"),
    ]
    try:
        for number in range(1, 101):
            email = f"demo-customer-{number:03d}@example.com"
            customer = db.execute(select(Customer).where(Customer.email == email)).scalar_one_or_none()
            if customer is None:
                customer = Customer(
                    name=f"Demo Customer {number:03d}",
                    email=email,
                    company=f"Demo Company {number:03d}",
                )
                db.add(customer)
                db.flush()
                created_customers += 1
            for ticket_number, (title, description, priority, status) in enumerate(scenarios, start=1):
                ticket_title = f"{title} #{ticket_number}"
                exists = db.execute(select(Ticket.id).where(
                    Ticket.customer_id == customer.id,
                    Ticket.title == ticket_title,
                )).first()
                if exists is None:
                    db.add(Ticket(
                        customer_id=customer.id,
                        title=ticket_title,
                        description=description,
                        priority=priority,
                        status=status,
                    ))
                    created_tickets += 1
        db.commit()
        print(f"Added {created_customers} demo customers and {created_tickets} demo tickets.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_scale()
