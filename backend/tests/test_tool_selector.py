"""Data-tool-selector tests.

Model calls are mocked through the shared `complete_json` seam; the
live check is opt-in in tests/test_live_groq.py.
"""

from unittest.mock import patch

from app.schemas.tool_call import ToolCall
from app.services.tool_selector import select_data_tool


def test_select_customer_tickets():
    tool_call = ToolCall(
        tool_name="get_customer_tickets",
        customer_id=1,
        ticket_id=None,
        reason="Customer tickets requested.",
    )

    with patch(
        "app.services.tool_selector.complete_json",
        return_value=tool_call,
    ) as mock_complete:
        result = select_data_tool("Show me the tickets for customer 1.")

    assert result.tool_name == "get_customer_tickets"
    assert result.customer_id == 1
    assert result.ticket_id is None
    mock_complete.assert_called_once()


def test_select_ticket():
    tool_call = ToolCall(
        tool_name="get_ticket",
        customer_id=None,
        ticket_id=1,
        reason="Ticket status requested.",
    )

    with patch(
        "app.services.tool_selector.complete_json",
        return_value=tool_call,
    ):
        result = select_data_tool("What is the status of ticket 1?")

    assert result.tool_name == "get_ticket"
    assert result.ticket_id == 1
    assert result.customer_id is None


def test_select_open_tickets():
    tool_call = ToolCall(
        tool_name="list_open_tickets",
        customer_id=None,
        ticket_id=None,
        reason="All open tickets requested.",
    )

    with patch(
        "app.services.tool_selector.complete_json",
        return_value=tool_call,
    ):
        result = select_data_tool("Show me all open tickets.")

    assert result.tool_name == "list_open_tickets"
    assert result.customer_id is None
    assert result.ticket_id is None
