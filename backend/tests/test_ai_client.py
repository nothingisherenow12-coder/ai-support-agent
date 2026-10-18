"""Tests for the shared Groq AI client.

These mock the provider entirely (no quota consumed) and assert that
provider failures become the AIError family rather than fake answers.
"""

import json

import pytest
from pydantic import BaseModel

from app.services import ai_client
from app.services.ai_client import (
    AIError,
    AIQuotaExceeded,
    AIUnauthorized,
    complete_json,
)


class SampleModel(BaseModel):
    intent: str
    confidence: float


def _fake_response(payload: str):
    from types import SimpleNamespace

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=payload)
            )
        ]
    )


class FakeCompletions:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def create(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._result


def _fake_client(result=None, error=None):
    from types import SimpleNamespace

    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=FakeCompletions(result=result, error=error)
        )
    )


def test_complete_json_parses_and_validates(monkeypatch):
    payload = json.dumps({"intent": "knowledge", "confidence": 0.8})
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(result=_fake_response(payload))
    )

    result = complete_json("system", "user", SampleModel)

    assert isinstance(result, SampleModel)
    assert result.intent == "knowledge"
    assert result.confidence == 0.8


def test_malformed_json_raises_ai_error(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "get_groq_client",
        lambda: _fake_client(result=_fake_response("not json at all")),
    )

    with pytest.raises(AIError):
        complete_json("system", "user", SampleModel)


def test_schema_mismatch_raises_ai_error(monkeypatch):
    payload = json.dumps({"intent": "knowledge"})
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(result=_fake_response(payload))
    )

    with pytest.raises(AIError):
        complete_json("system", "user", SampleModel)


def test_empty_response_raises_ai_error(monkeypatch):
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(result=_fake_response(""))
    )

    with pytest.raises(AIError):
        complete_json("system", "user", SampleModel)


def test_authentication_error_maps_to_unauthorized(monkeypatch):
    from groq import AuthenticationError

    error = AuthenticationError(
        "bad key",
        response=_dummy_response(401),
        body=None,
    )
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(error=error)
    )

    with pytest.raises(AIUnauthorized):
        complete_json("system", "user", SampleModel)


def test_rate_limit_maps_to_quota(monkeypatch):
    from groq import RateLimitError

    error = RateLimitError(
        "slow down",
        response=_dummy_response(429),
        body=None,
    )
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(error=error)
    )

    with pytest.raises(AIQuotaExceeded):
        complete_json("system", "user", SampleModel)


def test_connection_error_maps_to_ai_error(monkeypatch):
    from groq import APIConnectionError

    error = APIConnectionError(request=_dummy_request())
    monkeypatch.setattr(
        ai_client, "get_groq_client", lambda: _fake_client(error=error)
    )

    with pytest.raises(AIError):
        complete_json("system", "user", SampleModel)


def test_missing_key_raises_unauthorized(monkeypatch):
    monkeypatch.setattr(ai_client.settings, "groq_api_key", "")
    ai_client.reset_groq_client()

    with pytest.raises(AIUnauthorized):
        ai_client.get_groq_client()

    ai_client.reset_groq_client()


def _dummy_request():
    import httpx

    return httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def _dummy_response(status_code):
    import httpx

    return httpx.Response(
        status_code=status_code,
        request=_dummy_request(),
    )
