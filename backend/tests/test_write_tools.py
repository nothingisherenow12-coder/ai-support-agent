from app.db.database import SessionLocal
from app.services.tools.write_tools import create_ticket


def test_create_ticket():
    db = SessionLocal()

    try:
        result = create_ticket(
            db=db,
            customer_id=1,
            title="Test ticket",
            description="This ticket was created by an automated test.",
            priority="medium",
        )

        assert result["id"] is not None
        assert result["customer_id"] == 1
        assert result["title"] == "Test ticket"
        assert result["description"] == (
            "This ticket was created by an automated test."
        )
        assert result["priority"] == "medium"
        assert result["status"] == "open"

    finally:
        db.rollback()
        db.close()