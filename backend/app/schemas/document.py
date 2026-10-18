from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    id:int
    filename:str
    chunks_created:int
