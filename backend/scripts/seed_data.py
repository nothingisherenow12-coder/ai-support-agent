from app.db.database import SessionLocal
from app.models.customer import Customer
from app.models.ticket import Ticket
from sqlalchemy import select


def seed_data():
    db = SessionLocal()

    try:
        customers = [
            ("John Smith", "john@example.com", "Acme Inc"),
            ("Sarah Wilson", "sarah@example.com", "TechFlow"),
        ]
        saved = {}
        for name, email, company in customers:
            customer = db.execute(select(Customer).where(Customer.email == email)).scalar_one_or_none()
            if customer is None:
                customer = Customer(name=name, email=email, company=company)
                db.add(customer)
                db.flush()
            saved[email] = customer

        tickets = [
            ("john@example.com", "Login problem", "Customer cannot log in to the dashboard.", "high", "open"),
            ("john@example.com", "Billing issue", "Customer has a question about an unexpected charge.", "medium", "open"),
            ("sarah@example.com", "Password reset", "Customer requested help resetting their password.", "low", "resolved"),
        ]
        for email, title, description, priority, status in tickets:
            customer = saved[email]
            exists = db.execute(select(Ticket.id).where(Ticket.customer_id == customer.id, Ticket.title == title)).first()
            if exists is None:
                db.add(Ticket(customer_id=customer.id, title=title, description=description, priority=priority, status=status))
        db.commit()

        print("Seed data created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
