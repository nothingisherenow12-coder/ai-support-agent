"""Opt-in live Groq checks.

These make real API calls and consume the free-tier quota, so they are
skipped unless RUN_LIVE_AI_TESTS=1 is set. Run explicitly:

    $env:RUN_LIVE_AI_TESTS="1"; .\\.venv\\Scripts\\python.exe -m pytest tests/test_live_groq.py -v

All other test files mock the provider.
"""

import os

import pytest

from app.core.config import settings
from app.services.ai_client import (
    AIError,
    AIQuotaExceeded,
    AIUnauthorized,
    complete_json,
)
from app.schemas.intent import IntentClassification

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_AI_TESTS") != "1",
    reason="Live AI tests are opt-in (set RUN_LIVE_AI_TESTS=1).",
)


@pytest.fixture(autouse=True)
def _require_key():
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY is not configured.")


def test_live_intent_classification():
    from app.services.intent_classifier import classify_intent

    try:
        result = classify_intent("What is our refund policy?")
    except AIQuotaExceeded:
        pytest.skip("Groq quota exhausted.")
    except (AIUnauthorized, AIError) as exc:
        pytest.fail(f"Live Groq call failed: {type(exc).__name__}")

    assert result.intent in {"knowledge", "data", "action"}
    assert 0.0 <= result.confidence <= 1.0


def test_live_structured_json_roundtrip():
    try:
        result = complete_json(
            system_prompt=(
                "Return ONLY a JSON object with keys intent, confidence, reason. "
                "intent must be exactly one of: knowledge, data, action. "
                "confidence must be a number between 0 and 1. "
                "reason must be a short string."
            ),
            user_message="Classify: show me all open tickets.",
            response_model=IntentClassification,
        )
    except AIQuotaExceeded:
        pytest.skip("Groq quota exhausted.")
    except (AIUnauthorized, AIError) as exc:
        pytest.fail(f"Live Groq call failed: {type(exc).__name__}")

    assert isinstance(result, IntentClassification)
