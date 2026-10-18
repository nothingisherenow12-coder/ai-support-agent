from app.schemas.tool_call import ToolCall
from app.services.ai_client import complete_json

SYSTEM_PROMPT = """You are the data-tool selector for an AI Support & Operations Agent.

Choose exactly one tool.

Allowed tools:

get_customer
- Use when the user wants information about one customer.
- Requires customer_id.

get_customer_tickets
- Use when the user wants tickets belonging to one customer.
- Requires customer_id.

get_ticket
- Use when the user asks about one specific ticket.
- Requires ticket_id.

list_open_tickets
- Use when the user wants all currently open tickets.
- Requires no ID.

Rules:
- Only select one allowed tool.
- Do not execute the tool.
- Never invent customer_id or ticket_id.
- If an ID is not present, return null for that ID.
- Return a short reason.
- Return ONLY a JSON object with the keys: tool_name, customer_id, ticket_id, reason."""

def select_data_tool(
    user_message: str,
) -> ToolCall:
    if not user_message.strip():
        raise ValueError("User message cannot be empty.")

    result = complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=ToolCall,
    )
    assert isinstance(result, ToolCall)
    return result