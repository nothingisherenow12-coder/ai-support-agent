"""Shared Groq chat-completion client for structured AI tasks.

All generation tasks (intent classification, tool selection, action
planning, grounded answers) go through `complete_json`, which requests
JSON mode and validates the response against a Pydantic model before
any caller may use it. Provider failures are translated into the small
exception hierarchy below so routers can map them to HTTP statuses
without importing the Groq SDK.

Embeddings intentionally live elsewhere (Gemini): Groq has no
embeddings API, so `embedding.py` keeps using Gemini.
"""

import json
import logging

from groq import (
    Groq,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    """The AI provider failed in a way the caller cannot fix."""


class AIQuotaExceeded(AIError):
    """Provider rate limit / quota exhausted (maps to HTTP 503)."""


class AIUnauthorized(AIError):
    """Bad or missing API credentials (server misconfiguration)."""


_client: Groq | None = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise AIUnauthorized("GROQ_API_KEY is not configured.")
        _client = Groq(
            api_key=settings.groq_api_key,
            timeout=settings.groq_timeout_seconds,
        )
    return _client


def reset_groq_client() -> None:
    """Drop the cached client (used by tests)."""
    global _client
    _client = None


def complete_json(
    system_prompt: str,
    user_message: str,
    response_model: type[BaseModel],
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> BaseModel:
    """Ask the model for a JSON object and validate it.

    Raises AIUnauthorized, AIQuotaExceeded, or AIError on provider
    problems, malformed JSON, or schema mismatches. Never returns
    unvalidated data.
    """
    try:
        response = get_groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    except AuthenticationError as exc:
        raise AIUnauthorized("AI provider credentials were rejected.") from exc
    except RateLimitError as exc:
        raise AIQuotaExceeded("AI provider quota exhausted.") from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise AIError("AI provider is unreachable.") from exc
    except APIStatusError as exc:
        raise AIError("AI provider request failed.") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise AIError("AI provider returned an empty response.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("AI provider returned non-JSON content.")
        raise AIError("AI provider returned a malformed response.") from exc

    try:
        return response_model.model_validate(data)
    except ValidationError as exc:
        logger.warning("AI provider response failed schema validation.")
        raise AIError("AI provider returned an unexpected response.") from exc
