from app.db.database import SessionLocal
from app.services.tools.ticket_tools import (get_ticket,list_open_tickets)


def test_get_ticket():
    db = SessionLocal()

    try:
        ticket = get_ticket(
            db=db,
            ticket_id=1,
        )

        assert ticket is not None
        assert ticket["id"] == 1
        assert ticket["customer_id"] == 1
        assert ticket["title"] == "Login problem"
        assert ticket["status"] == "open"

    finally:
        db.close()

def test_list_open_tickets():
    db = SessionLocal()

    try:
        tickets = list_open_tickets(db=db)

        assert len(tickets) > 0

        for ticket in tickets:
            assert ticket["status"] == "open"

    finally:
        db.close()