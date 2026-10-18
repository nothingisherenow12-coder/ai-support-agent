from sqlalchemy.orm import Session
from app.schemas.tool_call import ToolCall
from app.services.tools.customer_tools import (get_customer,get_customer_tickets,)
from app.services.tools.ticket_tools import (get_ticket,list_open_tickets,)

def execute_tool(
    db: Session,
    tool_call: ToolCall,
) -> dict:
    if tool_call.tool_name == "get_customer":
        if tool_call.customer_id is None:
            raise ValueError("customer_id is required for get_customer.")

        result = get_customer(
            db=db,
            customer_id=tool_call.customer_id,
        )

        return {
            "tool": tool_call.tool_name,
            "result": result,
        }

    if tool_call.tool_name == "get_customer_tickets":
        if tool_call.customer_id is None:
            raise ValueError(
                "customer_id is required for get_customer_tickets."
            )

        result = get_customer_tickets(
            db=db,
            customer_id=tool_call.customer_id,
        )

        return {
            "tool": tool_call.tool_name,
            "result": result,
        }

    if tool_call.tool_name == "get_ticket":
        if tool_call.ticket_id is None:
            raise ValueError("ticket_id is required for get_ticket.")

        result = get_ticket(
            db=db,
            ticket_id=tool_call.ticket_id,
        )

        return {
            "tool": tool_call.tool_name,
            "result": result,
        }

    if tool_call.tool_name == "list_open_tickets":
        result = list_open_tickets(db=db)

        return {
            "tool": tool_call.tool_name,
            "result": result,
        }

    raise ValueError(
        f"Unsupported tool: {tool_call.tool_name}"
    )