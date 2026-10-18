from unittest.mock import MagicMock, patch
from app.schemas.action import ActionProposal
from app.db.database import SessionLocal
from app.schemas.intent import IntentClassification
from app.services.orchestrator import handle_user_message


def test_knowledge_request():
    db = SessionLocal()

    try:
        fake_classification = IntentClassification(
            intent="knowledge",
            confidence=1.0,
            reason="Test knowledge request.",
        )

        with patch(
            "app.services.orchestrator.classify_intent",
            return_value=fake_classification,
        ), patch(
            "app.services.orchestrator.search_similar_chunks",
            return_value=[],
        ), patch(
            "app.services.orchestrator.generate_grounded_answer",
            return_value=MagicMock(answer="I don't have enough information in the knowledge base to answer that.", sources=[], answerable=False),
        ):
            result = handle_user_message(
                db=db,
                message="What programming languages are listed on the resume?",
            )

        assert result.intent == "knowledge"
        assert result.requires_approval is False
        assert result.answer

    finally:
        db.close()


def test_action_without_customer_requests_clarification_without_saving():
    db = SessionLocal()
    proposal = ActionProposal(
        action_type="create_ticket", customer_id=None, title="Billing issue",
        description="Customer reports a billing issue.", reason="User request.",
    )
    classification = IntentClassification(intent="action", confidence=1.0, reason="action")
    try:
        with (
            patch("app.services.orchestrator.classify_intent", return_value=classification),
            patch("app.services.orchestrator.plan_action", return_value=proposal),
            patch("app.services.orchestrator.save_action_proposal") as save,
        ):
            result = handle_user_message(db, "Create a ticket for a billing issue")
        assert result.action_id is None
        assert "customer ID" in result.answer
        save.assert_not_called()
    finally:
        db.close()


def test_customer_tickets_request():
    db = SessionLocal()

    try:
        fake_classification = IntentClassification(
            intent="data",
            confidence=1.0,
            reason="Test data request.",
        )

        with patch(
            "app.services.orchestrator.classify_intent",
            return_value=fake_classification,
        ):
            result = handle_user_message(
                db=db,
                message="Show me the tickets for customer 1.",
            )

        assert result.intent == "data"
        assert result.requires_approval is False
        assert isinstance(result.data, list)
        assert len(result.data) > 0

        for ticket in result.data:
            assert ticket["customer_id"] == 1

    finally:
        db.close()


def test_ticket_request():
    db = SessionLocal()

    try:
        fake_classification = IntentClassification(
            intent="data",
            confidence=1.0,
            reason="Test data request.",
        )

        with patch(
            "app.services.orchestrator.classify_intent",
            return_value=fake_classification,
        ):
            result = handle_user_message(
                db=db,
                message="What is the status of ticket 1?",
            )

        assert result.intent == "data"
        assert result.requires_approval is False
        assert result.data["id"] == 1

    finally:
        db.close()


def test_open_tickets_request():
    db = SessionLocal()

    try:
        fake_classification = IntentClassification(
            intent="data",
            confidence=1.0,
            reason="Test data request.",
        )

        with patch(
            "app.services.orchestrator.classify_intent",
            return_value=fake_classification,
        ):
            result = handle_user_message(
                db=db,
                message="Show me all open tickets.",
            )

        assert result.intent == "data"
        assert result.requires_approval is False
        assert isinstance(result.data, list)

        for ticket in result.data:
            assert ticket["status"] == "open"

    finally:
        db.close()


def test_action_request():
    db = SessionLocal()

    try:
        fake_classification = IntentClassification(
            intent="action",
            confidence=1.0,
            reason="Test action request.",
        )

        fake_proposal = ActionProposal(
            action_type="create_ticket",
            customer_id=1,
            title="Login issue",
            description="John Smith cannot log in.",
            reason="User requested a support ticket.",
        )

        fake_saved_action = MagicMock()
        fake_saved_action.id = 123

        with (
            patch(
                "app.services.orchestrator.classify_intent",
                return_value=fake_classification,
            ),
            patch(
                "app.services.orchestrator.plan_action",
                return_value=fake_proposal,
            ),
            patch(
                "app.services.orchestrator.save_action_proposal",
                return_value=fake_saved_action,
            ) as mock_save,
        ):
            result = handle_user_message(
                db=db,
                message="Create a support ticket for John Smith.",
            )

        assert result.intent == "action"
        assert result.requires_approval is True
        assert result.action is not None
        assert result.action.title == "Login issue"
        assert result.action_id == 123

        mock_save.assert_called_once_with(
            db=db,
            proposal=fake_proposal,
        )

    finally:
        db.close()
