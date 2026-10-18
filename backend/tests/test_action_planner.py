from unittest.mock import patch

from app.schemas.action import ActionProposal
from app.services.action_planner import plan_action


def test_plan_create_ticket_action():
    fake_proposal = ActionProposal(
        action_type="create_ticket",
        customer_id=1,
        title="Billing issue",
        description="Customer reported a billing problem.",
        reason="User requested a support ticket.",
        requires_approval=True,
    )

    with patch(
        "app.services.action_planner.complete_json",
        return_value=fake_proposal,
    ) as mock_complete:
        result = plan_action(
            "Create a support ticket for customer 1 about a billing issue."
        )

    assert result.action_type == "create_ticket"
    assert result.customer_id == 1
    assert result.title == "Billing issue"
    assert result.description == "Customer reported a billing problem."
    assert result.requires_approval is True

    mock_complete.assert_called_once()


def test_plan_action_does_not_invent_customer_id():
    fake_proposal = ActionProposal(
        action_type="create_ticket",
        customer_id=None,
        title="Billing issue",
        description="Customer reported a billing problem.",
        reason="No customer ID was provided.",
        requires_approval=True,
    )

    with patch(
        "app.services.action_planner.complete_json",
        return_value=fake_proposal,
    ):
        result = plan_action("Create a support ticket about a billing issue.")

    assert result.customer_id is None
    assert result.requires_approval is True