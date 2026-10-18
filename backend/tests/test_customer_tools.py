from app.db.database import SessionLocal
from app.services.tools.customer_tools import (
    get_customer,
    get_customer_tickets,
)


def test_get_customer():
    db = SessionLocal()

    try:
        customer = get_customer(
            db=db,
            customer_id=1,
        )

        assert customer is not None
        assert customer["id"] == 1
        assert customer["name"] == "John Smith"
        assert customer["email"] == "john@example.com"
        assert customer["company"] == "Acme Inc"

    finally:
        db.close()


def test_get_customer_tickets():
    db = SessionLocal()

    try:
        tickets = get_customer_tickets(
            db=db,
            customer_id=1,
        )

        assert len(tickets) > 0

        for ticket in tickets:
            assert ticket["customer_id"] == 1
            assert "title" in ticket
            assert "status" in ticket
            assert "priority" in ticket

    finally:
        db.close()