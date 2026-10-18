from types import SimpleNamespace

import pytest

from app.services import retrieval


class FakeDB:
    def __init__(self, rows): self.rows = rows; self.statement = None
    def execute(self, statement): self.statement = statement; return self
    def all(self): return self.rows


def test_search_similar_chunks_returns_ranked_rows(monkeypatch):
    monkeypatch.setattr(retrieval, "generate_query_embedding", lambda _query: [0.1] * 768)
    chunk = SimpleNamespace(id=4, content="A support policy passage.")
    db = FakeDB([(chunk, 0.12)])
    result = retrieval.search_similar_chunks(db, "support policy", top_k=4)
    assert result[0].chunk is chunk
    assert result[0].distance == pytest.approx(0.12)
    assert db.statement is not None


def test_search_collapses_repeated_passages(monkeypatch):
    monkeypatch.setattr(retrieval, "generate_query_embedding", lambda _query: [0.1] * 768)
    repeated_a = SimpleNamespace(id=1, content="Skills: Python, SQL")
    repeated_b = SimpleNamespace(id=2, content="  Skills: Python, SQL  ")
    distinct = SimpleNamespace(id=3, content="Experience: backend engineering")
    db = FakeDB([(repeated_a, 0.1), (repeated_b, 0.11), (distinct, 0.2)])

    result = retrieval.search_similar_chunks(db, "resume skills", top_k=3)

    assert [item.chunk.id for item in result] == [1, 3]


@pytest.mark.parametrize("query,top_k", [("", 3), ("question", 0)])
def test_invalid_search_inputs_fail_before_embedding(monkeypatch, query, top_k):
    monkeypatch.setattr(retrieval, "generate_query_embedding", lambda _query: pytest.fail("should not embed"))
    with pytest.raises(ValueError):
        retrieval.search_similar_chunks(FakeDB([]), query, top_k)
