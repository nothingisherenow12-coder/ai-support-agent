from google import genai
from google.genai import types
from app.core.config import settings

MODEL_NAME = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768

client = genai.Client(
    api_key=settings.gemini_api_key,
)
def _generate_embedding(text: str,task_type:str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION,
            task_type=task_type
        ),
    )
    return response.embeddings[0].values

def generate_document_embedding(text:str) -> list[float]:
    """
    generate an embedding for a knowledge-base document chunk"""

    return _generate_embedding(
        text=text,
        task_type="RETRIEVAL_DOCUMENT",

    )
def generate_query_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a user's retrieval query.
    """

    return _generate_embedding(
        text=text,
        task_type="RETRIEVAL_QUERY",
    )