from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.customer import Customer


client = TestClient(app)


def test_create_customer_through_api_and_reject_duplicate_email():
    email = f"frontend-{uuid4().hex}@example.test"
    response = client.post(
        "/api/v1/customers",
        json={"name": "Frontend Customer", "email": email, "company": "Example Co"},
    )
    assert response.status_code == 201
    customer_id = response.json()["id"]
    assert response.json()["email"] == email

    duplicate = client.post(
        "/api/v1/customers",
        json={"name": "Another Name", "email": email},
    )
    assert duplicate.status_code == 409

    db = SessionLocal()
    try:
        customer = db.get(Customer, customer_id)
        assert customer is not None
        db.delete(customer)
        db.commit()
    finally:
        db.close()
