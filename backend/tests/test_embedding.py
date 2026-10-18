from types import SimpleNamespace

from app.services import embedding


def test_document_embedding_uses_document_task(monkeypatch):
    calls = []
    monkeypatch.setattr(embedding, "client", SimpleNamespace(models=SimpleNamespace(embed_content=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1] * 768)]))))
    result = embedding.generate_document_embedding("policy text")
    assert len(result) == 768
    assert calls[0]["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_query_embedding_uses_query_task(monkeypatch):
    calls = []
    monkeypatch.setattr(embedding, "client", SimpleNamespace(models=SimpleNamespace(embed_content=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(embeddings=[SimpleNamespace(values=[0.2] * 768)]))))
    result = embedding.generate_query_embedding("refund time")
    assert len(result) == 768
    assert calls[0]["config"].task_type == "RETRIEVAL_QUERY"
