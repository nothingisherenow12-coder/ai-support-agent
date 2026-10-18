from sqlalchemy.orm import Session
from app.schemas.orchestrator import OrchestratorResponse
from app.services.intent_classifier import classify_intent
from app.services.rag import generate_grounded_answer
from app.services.retrieval import search_similar_chunks
from app.services.tool_executor import execute_tool
from app.services.tool_selector import select_data_tool
from app.services.action_planner import plan_action
from app.services.action_service import save_action_proposal

def handle_user_message(
    db: Session,
    message: str,
    context: list[str] | None = None,
) -> OrchestratorResponse:
    
    classification = classify_intent(message)

    if classification.intent == "knowledge":
        contextual_question = "\n".join(
            [f"Recent conversation: {item[:1000]}" for item in (context or [])[-6:]]
            + [f"Current question: {message}"]
        )
        results = search_similar_chunks(
            db=db,
            query=contextual_question,
            top_k=5,
        )

        rag_result = generate_grounded_answer(
            question=contextual_question,
            retrieved_chunks=results,
        )
        
        return OrchestratorResponse(
            intent="knowledge",
            answer=rag_result.answer,
            sources=[
                {
                    "document_id": source.document_id,
                    "filename": source.filename,
                    "chunk_id": source.chunk_id,
                    "chunk_index": source.chunk_index,
                    "distance": source.distance,
                }
                for source in rag_result.sources
            ],
        )
    if classification.intent == "data":
        tool_call = select_data_tool(message)

        tool_result = execute_tool(
            db=db,
            tool_call=tool_call,
        )

        return OrchestratorResponse(
            intent="data",
            answer=f"Data retrieved using {tool_result['tool']}.",
            data=tool_result["result"],
        )
    
    if classification.intent == "action":
        
        proposal = plan_action(message)

        if proposal.customer_id is None:
            return OrchestratorResponse(
                intent="action",
                answer="Which customer ID should I use? I need that before I can prepare the ticket proposal.",
                requires_approval=True,
                action=proposal,
            )

        saved_action = save_action_proposal(
            db=db,
            proposal=proposal,
        )

        return OrchestratorResponse(
            intent="action",
            answer=(
                "Action proposal saved. Review it before "
                "approving execution."
            ),
            requires_approval=True,
            action=proposal,
            action_id=saved_action.id,
        )
