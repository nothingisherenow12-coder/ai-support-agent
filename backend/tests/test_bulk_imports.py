from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_customer_import_previews_then_skips_reimported_email():
    suffix = uuid4().hex
    email = f"bulk-{suffix}@example.com"
    content = f"name,email,company\nBulk Test {suffix[:8]},{email},Example Co\n".encode()

    preview = client.post("/api/v1/imports/customers", files={"file": ("customers.csv", content, "text/csv")})
    assert preview.status_code == 200
    assert preview.json()["ready_to_import"] == 1
    assert preview.json()["total_rows"] == 1

    imported = client.post("/api/v1/imports/customers?dry_run=false", files={"file": ("customers.csv", content, "text/csv")})
    assert imported.status_code == 200
    assert imported.json()["imported"] == 1

    repeated = client.post("/api/v1/imports/customers", files={"file": ("customers.csv", content, "text/csv")})
    assert repeated.status_code == 200
    assert repeated.json()["ready_to_import"] == 0
    assert repeated.json()["skipped_duplicates"] == 1


def test_ticket_import_requires_stable_id_and_is_idempotent():
    suffix = uuid4().hex
    customer_email = f"ticket-bulk-{suffix}@example.com"
    customer_csv = f"name,email\nBulk Ticket Customer,{customer_email}\n".encode()
    customer_result = client.post("/api/v1/imports/customers?dry_run=false", files={"file": ("customers.csv", customer_csv, "text/csv")})
    assert customer_result.status_code == 200

    external_id = f"source-{suffix}"
    ticket_csv = f"external_id,customer_email,title,description,priority,status\n{external_id},{customer_email},Import test,CSV import test,medium,open\n".encode()
    imported = client.post("/api/v1/imports/tickets?dry_run=false", files={"file": ("tickets.csv", ticket_csv, "text/csv")})
    assert imported.status_code == 200
    assert imported.json()["imported"] == 1

    repeated = client.post("/api/v1/imports/tickets", files={"file": ("tickets.csv", ticket_csv, "text/csv")})
    assert repeated.status_code == 200
    assert repeated.json()["ready_to_import"] == 0
    assert repeated.json()["skipped_duplicates"] == 1


def test_customer_and_ticket_list_endpoints_paginate():
    customers = client.get("/api/v1/customers", params={"limit": 2, "offset": 0})
    assert customers.status_code == 200
    assert len(customers.json()["items"]) <= 2
    assert customers.json()["total"] >= len(customers.json()["items"])

    tickets = client.get("/api/v1/tickets", params={"limit": 2, "offset": 0})
    assert tickets.status_code == 200
    assert len(tickets.json()["items"]) <= 2
    assert tickets.json()["total"] >= len(tickets.json()["items"])
