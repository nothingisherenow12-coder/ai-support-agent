
import pytest
from pydantic import ValidationError

from app.schemas.action import ActionProposal


def test_action_proposal():
    proposal = ActionProposal(
        action_type="create_ticket",
        customer_id=1,
        title="Billing issue",
        description="Customer reported a billing problem.",
        reason="User requested a support ticket.",
    )

    assert proposal.action_type == "create_ticket"
    assert proposal.customer_id == 1
    assert proposal.title == "Billing issue"
    assert proposal.requires_approval is True


def test_action_proposal_rejects_status_field():
    with pytest.raises(ValidationError):
        ActionProposal(
            action_type="create_ticket",
            customer_id=1,
            title="Billing issue",
            description="Customer reported a billing problem.",
            reason="User requested a support ticket.",
            status="approved",
        )


def test_action_proposal_rejects_empty_title():
    with pytest.raises(ValidationError):
        ActionProposal(
            action_type="create_ticket",
            customer_id=1,
            title="",
            description="Customer reported a billing problem.",
            reason="User requested a support ticket.",
        )
