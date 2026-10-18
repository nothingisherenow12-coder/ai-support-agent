from app.models.document_chunk import DocumentChunk
from app.services import document_service


class FakeDB:
    def __init__(self): self.added = []; self.flushes = 0; self.commits = 0
    def add_all(self, rows): self.added.extend(rows)
    def flush(self): self.flushes += 1
    def commit(self): self.commits += 1
    def refresh(self, _row): pass


def test_save_document_chunks_flushes_without_owning_transaction(monkeypatch):
    monkeypatch.setattr(document_service, "generate_document_embedding", lambda text: [float(len(text))])
    db = FakeDB()
    rows = document_service.save_document_chunks(db, 17, ["first", "second"])
    assert len(rows) == 2
    assert all(isinstance(row, DocumentChunk) for row in rows)
    assert [row.chunk_index for row in rows] == [0, 1]
    assert db.flushes == 1
    assert db.commits == 0
