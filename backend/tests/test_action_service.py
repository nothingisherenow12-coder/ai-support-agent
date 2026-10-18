from unittest.mock import MagicMock
from app.models.action import Action
from app.schemas.action import ActionProposal
from app.services.action_service import save_action_proposal

def test_save_action_proposal():
    db = MagicMock()

    proposal = ActionProposal(
        action_type="create_ticket",
        customer_id=1,
        title="Login issue",
        description="Customer cannot log in.",
        reason="User requested a support ticket.",
    )

    action = save_action_proposal(db, proposal)

    assert isinstance(action, Action)
    assert action.action_type == "create_ticket"
    assert action.customer_id == 1
    assert action.title == "Login issue"
    assert action.status == "proposed"

    db.add.assert_called_once_with(action)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(action)
