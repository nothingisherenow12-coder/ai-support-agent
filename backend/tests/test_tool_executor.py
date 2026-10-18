from app.db.database import SessionLocal
from app.schemas.tool_call import ToolCall
from app.services.tool_executor import execute_tool


def test_execute_get_customer():
    db = SessionLocal()

    try:
        tool_call = ToolCall(
            tool_name="get_customer",
            customer_id=1,
            ticket_id=None,
            reason="Get customer information.",
        )

        result = execute_tool(
            db=db,
            tool_call=tool_call,
        )

        assert result["tool"] == "get_customer"
        assert result["result"]["id"] == 1
        assert result["result"]["name"] == "John Smith"

    finally:
        db.close()


def test_execute_get_ticket():
    db = SessionLocal()

    try:
        tool_call = ToolCall(
            tool_name="get_ticket",
            customer_id=None,
            ticket_id=1,
            reason="Get ticket information.",
        )

        result = execute_tool(
            db=db,
            tool_call=tool_call,
        )

        assert result["tool"] == "get_ticket"
        assert result["result"]["id"] == 1

    finally:
        db.close()


def test_execute_list_open_tickets():
    db = SessionLocal()

    try:
        tool_call = ToolCall(
            tool_name="list_open_tickets",
            customer_id=None,
            ticket_id=None,
            reason="List open tickets.",
        )

        result = execute_tool(
            db=db,
            tool_call=tool_call,
        )

        assert result["tool"] == "list_open_tickets"
        assert isinstance(result["result"], list)

        for ticket in result["result"]:
            assert ticket["status"] == "open"

    finally:
        db.close()