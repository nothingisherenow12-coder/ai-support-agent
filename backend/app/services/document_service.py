from sqlalchemy.orm import Session 
from app.models.document_chunk import DocumentChunk
from app.services.embedding import generate_document_embedding

def save_document_chunks(
        db:Session,
        document_id:int,
        chunks=list[str],)-> list[DocumentChunk]:
    document_chunks=[]
    for index,content in enumerate(chunks):
        embedding=generate_document_embedding(content)
        document_chunk=DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        document_chunks.append(document_chunk)
    db.add_all(document_chunks)
    db.flush()

    for document_chunk in document_chunks:
        db.refresh(document_chunk)

    return document_chunks
       

