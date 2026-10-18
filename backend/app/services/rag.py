from pydantic import BaseModel
from dataclasses import dataclass
import re
from app.core.config import settings
from app.services.ai_client import complete_json
from app.services.retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are a support knowledge assistant.

Determine whether the provided knowledge-base context contains
enough information to directly answer the user's question.

Rules:
- Use ONLY the provided knowledge-base context.
- Do not use outside knowledge.
- Do not invent facts.
- For list, extract, and summary requests, answer from relevant facts even
  when the question uses different wording from the document.
- You may combine explicit facts from the same document for a summary, but do
  not infer relationships, dates, or details the document does not state.
- If the context does not contain facts that support the requested answer,
  set answerable to false.
- If the context directly answers the question, set answerable to true.
- If answerable is false, answer must be:
  "I don't have enough information in the knowledge base to answer that."
- Keep the answer concise.
- Return ONLY a JSON object with the keys: answerable, answer."""

class GroundedAnswer(BaseModel):
    answerable: bool
    answer: str

@dataclass
class RAGSource:
    document_id:int
    filename:str
    chunk_id:int
    chunk_index:int
    distance:float

@dataclass
class RAGResponse:
    answer:str
    sources:list[RAGSource]
    answerable:bool 


def generate_grounded_answer(
        question:str,
        retrieved_chunks:list[RetrievedChunk],
) -> RAGResponse:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not retrieved_chunks:
        return RAGResponse(
            answer="I don't have enough information in the knowledge base to answer that.",
            sources=[],
            answerable=False,
        )
    
    # Filename-scoped resume retrieval is already limited to the requested
    # document type. Let the grounded model inspect those candidates instead
    # of dropping useful resume sections at the generic similarity cutoff.
    is_resume_question = bool(
        re.search(r"\b(resume|resumes|cv|cvs|curriculum vitae)\b", question, re.IGNORECASE)
    )
    relevant_chunks = (
        retrieved_chunks
        if is_resume_question
        else [
            result
            for result in retrieved_chunks
            if result.distance <= settings.rag_max_distance
        ]
    )


    if not relevant_chunks:
        return RAGResponse(
            answer="I don't have enough information in the knowledge base to answer that.",
            sources=[],
            answerable=False,
        )
    context_parts=[]

    for result in relevant_chunks:
        context_parts.append(
            f"[Source chunk {result.chunk.chunk_index}]\n"
            f"{result.chunk.content}"
        )

    context="\n\n".join(context_parts)
    grounded_answer = complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=(
            f"Knowledge-base context:\n{context}\n\n"
            f"User question:\n{question}"
        ),
        response_model=GroundedAnswer,
    )
    assert isinstance(grounded_answer, GroundedAnswer)

    if not grounded_answer.answerable:
         return RAGResponse(
                answer="I don't have enough information in the knowledge base to answer that.",
                sources=[],
                answerable=False,
            )
   

    sources=[
        RAGSource(
            document_id=result.chunk.document.id,
            filename=result.chunk.document.filename,
            chunk_id=result.chunk.id,
            chunk_index=result.chunk.chunk_index,
            distance=result.distance,

        )
        for result in relevant_chunks
    ]
    return RAGResponse(
        answer=grounded_answer.answer,
        sources=sources,
        answerable=True,
    )




