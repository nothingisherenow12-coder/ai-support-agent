
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_client import AIError, AIQuotaExceeded
from google.genai.errors import ClientError
client = TestClient(app)


def test_chat_action_request_returns_proposal():
    fake_response = {
        "intent": "action",
        "answer": (
            "Action proposal saved. Review it before "
            "approving execution."
        ),
        "data": None,
        "sources": [],
        "requires_approval": True,
        "action": {
            "action_type": "create_ticket",
            "customer_id": 1,
            "title": "Login issue",
            "description": "The customer cannot log in.",
            "reason": "The user requested a support ticket.",
            "requires_approval": True,
        },
        "action_id": 123,
    }

    with patch(
        "app.routers.chat.handle_user_message",
        return_value=fake_response,
    ) as mock_orchestrator:
        response = client.post(
            "/api/v1/chat",
            json={
                "message": (
                    "Create a support ticket for customer 1."
                )
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert body["intent"] == "action"
    assert body["requires_approval"] is True
    assert body["action_id"] == 123
    assert body["action"]["action_type"] == "create_ticket"

    mock_orchestrator.assert_called_once()
    assert (
        mock_orchestrator.call_args.kwargs["message"]
        == "Create a support ticket for customer 1."
    )


def test_chat_rejects_missing_message():
    response = client.post(
        "/api/v1/chat",
        json={},
    )

    assert response.status_code == 422


def test_chat_data_request_returns_data():
    fake_response = {
        "intent": "data",
        "answer": "Data retrieved using get_customer_tickets.",
        "data": [
            {
                "id": 1,
                "customer_id": 1,
                "title": "Login issue",
                "description": "Customer cannot log in.",
                "priority": "medium",
                "status": "open",
            }
        ],
        "sources": [],
        "requires_approval": False,
        "action": None,
        "action_id": None,
    }

    with patch(
        "app.routers.chat.handle_user_message",
        return_value=fake_response,
    ) as mock_orchestrator:
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Show me the tickets for customer 1."
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert body["intent"] == "data"
    assert body["requires_approval"] is False
    assert isinstance(body["data"], list)
    assert body["data"][0]["customer_id"] == 1

    mock_orchestrator.assert_called_once()



def test_chat_knowledge_request_returns_answer_and_sources():
    fake_response = {
        "intent": "knowledge",
        "answer": "The refund policy allows eligible refunds within 30 days.",
        "data": None,
        "sources": [
            {
                "document_id": 7,
                "filename": "refund-policy.pdf",
                "chunk_id": 12,
                "chunk_index": 2,
                "distance": 0.15,
            }
        ],
        "requires_approval": False,
        "action": None,
        "action_id": None,
    }

    with patch(
        "app.routers.chat.handle_user_message",
        return_value=fake_response,
    ) as mock_orchestrator:
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "What is our refund policy?"
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert body["intent"] == "knowledge"
    assert body["answer"]
    assert len(body["sources"]) == 1
    assert body["sources"][0]["filename"] == "refund-policy.pdf"
    assert body["requires_approval"] is False

    mock_orchestrator.assert_called_once()


def test_chat_handles_gemini_quota_error():
    gemini_error = ClientError(
        429,
        {
            "error": {
                "code": 429,
                "message": "Quota exceeded.",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )

    with patch(
        "app.routers.chat.handle_user_message",
        side_effect=gemini_error,
    ):
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "What is our refund policy?"
            },
        )

    assert response.status_code == 503
    assert "quota" in response.json()["detail"].lower()
    assert response.headers["retry-after"] == "3600"


def test_chat_handles_groq_quota_error():
    with patch(
        "app.routers.chat.handle_user_message",
        side_effect=AIQuotaExceeded("quota"),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "What is our refund policy?"},
        )

    assert response.status_code == 503
    assert "quota" in response.json()["detail"].lower()
    assert response.headers["retry-after"] == "3600"


def test_chat_handles_groq_provider_error():
    with patch(
        "app.routers.chat.handle_user_message",
        side_effect=AIError("provider down"),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "What is our refund policy?"},
        )

    assert response.status_code == 502
    assert "ai service" in response.json()["detail"].lower()
