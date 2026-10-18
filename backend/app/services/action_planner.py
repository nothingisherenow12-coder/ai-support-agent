from app.schemas.action import ActionProposal
from app.services.ai_client import complete_json


SYSTEM_PROMPT = """You are the action planner for an AI Support & Operations Agent.

Your job is to convert the user's request into a structured action proposal.

Currently, the only supported action is:

create_ticket
- Creates a support ticket for an existing customer.
- Requires customer_id.
- Requires a useful title.
- Requires a useful description.

Rules:
- Only propose create_ticket.
- Never execute the action.
- Never invent a customer_id.
- If the customer ID is not known, return null.
- The proposal must require approval.
- Keep the reason concise.
- Extract the ticket title and description from the user's request.
- If the request does not contain enough information for a meaningful
  ticket, still return a proposal with the information that is available.
- Return ONLY a JSON object with the keys: action_type, customer_id, title,
  description, reason, requires_approval."""


def plan_action(user_message: str) -> ActionProposal:
    if not user_message.strip():
        raise ValueError("User message cannot be empty.")

    result = complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=ActionProposal,
    )
    assert isinstance(result, ActionProposal)
    return result