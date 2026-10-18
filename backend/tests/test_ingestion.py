from app.services import ingestion


class FakeDB:
    def __init__(self): self.added = []; self.flushes = 0; self.rollbacks = 0; self.commits = 0
    def add(self, row): self.added.append(row)
    def flush(self): self.flushes += 1; self.added[0].id = 42
    def refresh(self, _row): pass
    def execute(self, _statement):
        class Result:
            @staticmethod
            def scalar_one_or_none(): return None
        return Result()
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def test_ingest_pdf_saves_document_and_chunks_atomically(tmp_path, monkeypatch):
    source = tmp_path / "guide.pdf"
    source.write_bytes(b"not parsed in this unit test")
    monkeypatch.setattr(ingestion, "extract_text_from_pdf", lambda _path: "support guide")
    monkeypatch.setattr(ingestion, "chunk_text", lambda _text: ["support", "guide"])
    saved = []
    monkeypatch.setattr(ingestion, "save_document_chunks", lambda **kwargs: saved.append(kwargs) or [])
    db = FakeDB()
    document = ingestion.ingest_pdf(db, str(source), "guide.pdf")
    assert document.id == 42
    assert saved == [{"db": db, "document_id": 42, "chunks": ["support", "guide"]}]
    assert db.rollbacks == 0
    assert db.commits == 1


def test_ingest_pdf_rolls_back_document_when_chunk_save_fails(tmp_path, monkeypatch):
    source = tmp_path / "guide.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(ingestion, "extract_text_from_pdf", lambda _path: "support guide")
    monkeypatch.setattr(ingestion, "chunk_text", lambda _text: ["support guide"])
    def fail(**_kwargs): raise RuntimeError("embedding unavailable")
    monkeypatch.setattr(ingestion, "save_document_chunks", fail)
    db = FakeDB()
    try:
        ingestion.ingest_pdf(db, str(source), "guide.pdf")
        assert False, "Expected the chunking error to propagate"
    except RuntimeError:
        pass
    assert db.rollbacks == 1
