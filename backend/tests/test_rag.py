"""Unit tests for the grounded-answer service.

All tests here avoid live Groq calls: the no-evidence paths never reach
the model, and the grounded path patches the shared AI client's
`complete_json` seam.
"""

from types import SimpleNamespace

from app.services.rag import GroundedAnswer, generate_grounded_answer
from app.services.retrieval import RetrievedChunk
from unittest.mock import patch


def make_chunk(chunk_id=1, chunk_index=0, content="Refunds are available within 30 days."):
    chunk = SimpleNamespace(
        id=chunk_id,
        chunk_index=chunk_index,
        content=content,
        document=SimpleNamespace(id=7, filename="refund-policy.pdf"),
    )
    return RetrievedChunk(chunk=chunk, distance=0.15)


def test_empty_retrieval_returns_unanswerable():
    result = generate_grounded_answer("What is the refund policy?", [])

    assert result.answerable is False
    assert result.sources == []
    assert "enough information" in result.answer


def test_distant_chunks_return_unanswerable():
    chunk = make_chunk()
    chunk.distance = 0.99

    result = generate_grounded_answer("What is the refund policy?", [chunk])

    assert result.answerable is False
    assert result.sources == []


def test_grounded_answer_uses_model_response():
    answer = GroundedAnswer(answerable=True, answer="Refunds within 30 days.")

    with patch("app.services.rag.complete_json", return_value=answer):
        result = generate_grounded_answer("What is the refund policy?", [make_chunk()])

    assert result.answerable is True
    assert result.answer == "Refunds within 30 days."
    assert len(result.sources) == 1
    assert result.sources[0].filename == "refund-policy.pdf"


def test_resume_questions_keep_relevant_chunks_past_generic_cutoff():
    chunk = make_chunk(content="Skills include Python, SQL, and cloud services.")
    chunk.distance = 0.62
    answer = GroundedAnswer(answerable=True, answer="Python, SQL, and cloud services.")

    with patch("app.services.rag.complete_json", return_value=answer) as mock_complete:
        result = generate_grounded_answer(
            "List the skills in the uploaded resume.",
            [chunk],
        )

    assert result.answerable is True
    assert result.answer == answer.answer
    mock_complete.assert_called_once()


def test_model_unanswerable_discards_sources():
    answer = GroundedAnswer(
        answerable=False,
        answer="I don't have enough information in the knowledge base to answer that.",
    )

    with patch("app.services.rag.complete_json", return_value=answer):
        result = generate_grounded_answer("Something unrelated?", [make_chunk()])

    assert result.answerable is False
    assert result.sources == []
