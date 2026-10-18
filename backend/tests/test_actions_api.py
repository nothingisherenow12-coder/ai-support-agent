"""API tests for the action lifecycle (real PostgreSQL, no AI calls).

Covers: propose -> approve -> execute -> ticket exists -> executed,
plus rejection, double-execution, unapproved-execution and 404 paths.
Rows created here are deleted afterwards so reruns stay clean.
"""

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.database import SessionLocal
from app.main import app
from app.models.action import Action
from app.models.ticket import Ticket

client = TestClient(app)

PROPOSAL = {
    "action_type": "create_ticket",
    "customer_id": 1,
    "title": "API lifecycle test ticket",
    "description": "Created by test_actions_api.",
    "reason": "Verify the approval lifecycle.",
    "requires_approval": True,
}


def cleanup(action_id=None, ticket_id=None):
    db = SessionLocal()
    try:
        if ticket_id is not None:
            db.execute(delete(Ticket).where(Ticket.id == ticket_id))
        if action_id is not None:
            db.execute(delete(Action).where(Action.id == action_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def test_full_approval_lifecycle():
    action_id = None
    ticket_id = None
    try:
        # Propose.
        response = client.post("/api/v1/actions", json=PROPOSAL)
        assert response.status_code == 201
        action_id = response.json()["id"]
        assert response.json()["status"] == "proposed"

        # Ticket must not exist before execution.
        assert client.get(f"/api/v1/actions/{action_id}").json()["status"] == "proposed"

        # Approve then execute.
        assert client.post(f"/api/v1/actions/{action_id}/approve").status_code == 200
        executed = client.post(f"/api/v1/actions/{action_id}/execute")
        assert executed.status_code == 200
        body = executed.json()
        assert body["action_status"] == "executed"
        ticket_id = body["ticket"]["id"]
        assert body["ticket"]["customer_id"] == 1

        # Action is marked executed.
        assert client.get(f"/api/v1/actions/{action_id}").json()["status"] == "executed"

        # Re-execution is rejected.
        again = client.post(f"/api/v1/actions/{action_id}/execute")
        assert again.status_code == 409
    finally:
        cleanup(action_id, ticket_id)


def test_execute_without_approval_is_rejected():
    action_id = None
    try:
        action_id = client.post("/api/v1/actions", json=PROPOSAL).json()["id"]
        response = client.post(f"/api/v1/actions/{action_id}/execute")
        assert response.status_code == 409
    finally:
        cleanup(action_id)


def test_reject_then_execute_is_rejected():
    action_id = None
    try:
        action_id = client.post("/api/v1/actions", json=PROPOSAL).json()["id"]
        assert client.post(f"/api/v1/actions/{action_id}/reject").status_code == 200
        assert client.post(f"/api/v1/actions/{action_id}/execute").status_code == 409
        # And it cannot be approved after rejection either.
        assert client.post(f"/api/v1/actions/{action_id}/approve").status_code == 409
    finally:
        cleanup(action_id)


def test_missing_action_returns_404():
    assert client.post("/api/v1/actions/999999/approve").status_code == 404
    assert client.post("/api/v1/actions/999999/reject").status_code == 404
    assert client.post("/api/v1/actions/999999/execute").status_code == 404
    assert client.get("/api/v1/actions/999999").status_code == 404


def test_propose_with_unknown_customer_is_rejected():
    response = client.post(
        "/api/v1/actions",
        json=dict(PROPOSAL, customer_id=999999),
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_list_filter_by_status():
    action_id = None
    try:
        action_id = client.post("/api/v1/actions", json=PROPOSAL).json()["id"]
        response = client.get("/api/v1/actions", params={"status": "proposed"})
        assert response.status_code == 200
        assert any(a["id"] == action_id for a in response.json())
    finally:
        cleanup(action_id)
