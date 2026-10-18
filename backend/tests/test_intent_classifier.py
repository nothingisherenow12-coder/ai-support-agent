"""Intent-classifier tests.

The model call is mocked via the shared `complete_json` seam so these
tests never consume API quota. Live end-to-end checks live in
tests/test_live_groq.py and are opt-in.
"""

from unittest.mock import patch

from app.schemas.intent import IntentClassification
from app.services.intent_classifier import classify_intent


def _classification(intent, confidence=0.9, reason="test"):
    return IntentClassification(
        intent=intent,
        confidence=confidence,
        reason=reason,
    )


def test_knowledge_intent():
    with patch(
        "app.services.intent_classifier.complete_json",
        return_value=_classification("knowledge"),
    ) as mock_complete:
        result = classify_intent("What is our refund policy?")

    assert result.intent == "knowledge"
    assert 0.0 <= result.confidence <= 1.0
    mock_complete.assert_called_once()


def test_resume_skills_question_routes_to_knowledge_without_model_call():
    with patch("app.services.intent_classifier.complete_json") as mock_complete:
        result = classify_intent("I need the skills of that person in the uploaded resume.")

    assert result.intent == "knowledge"
    mock_complete.assert_not_called()


def test_data_intent():
    with patch(
        "app.services.intent_classifier.complete_json",
        return_value=_classification("data"),
    ):
        result = classify_intent("Show me John Smith's tickets.")

    assert result.intent == "data"
    assert 0.0 <= result.confidence <= 1.0


def test_action_intent():
    with patch(
        "app.services.intent_classifier.complete_json",
        return_value=_classification("action"),
    ):
        result = classify_intent("Create a support ticket for John Smith.")

    assert result.intent == "action"
    assert 0.0 <= result.confidence <= 1.0


def test_ambiguous_intent_is_allowed():
    with patch(
        "app.services.intent_classifier.complete_json",
        return_value=_classification("knowledge", confidence=0.5),
    ):
        result = classify_intent("Can you help me with the customer thing?")

    assert result.intent in {"knowledge", "data", "action"}
    assert 0.0 <= result.confidence <= 1.0


def test_empty_message_rejected_without_model_call():
    with patch(
        "app.services.intent_classifier.complete_json"
    ) as mock_complete:
        try:
            classify_intent("   ")
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError for empty message")

    mock_complete.assert_not_called()
