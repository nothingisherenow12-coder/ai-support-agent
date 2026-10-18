from sqlalchemy import select
from sqlalchemy.orm import Session
import logging

from app.models.action import Action
from app.services.tools.write_tools import create_ticket

logger = logging.getLogger(__name__)


def execute_action(db: Session, action_id: int) -> dict:
    """Execute an approved action exactly once.

    The action row is locked (SELECT ... FOR UPDATE) so concurrent
    executions serialize: the loser sees status != "approved" and is
    rejected without creating a second ticket.

    Only actions in status "approved" may execute. Anything else raises
    ValueError (mapped to HTTP 409 by the router). A missing action
    raises LookupError (mapped to HTTP 404).

    The ticket creation and the status transition share one transaction:
    if ticket creation fails, the transaction rolls back and the action
    stays "approved" so it can be retried — never falsely "executed".
    """
    try:
        action = db.execute(
            select(Action).where(Action.id == action_id).with_for_update()
        ).scalar_one_or_none()

        if action is None:
            raise LookupError(f"Action {action_id} not found.")

        if action.status != "approved":
            raise ValueError(
                f"Action {action_id} must be approved before execution "
                f"(current status: '{action.status}')."
            )

        ticket = create_ticket(
            db=db,
            customer_id=action.customer_id,
            title=action.title,
            description=action.description,
        )

        action.status = "executed"
        db.commit()
        db.refresh(action)
        logger.info("action %s executed: ticket %s", action.id, ticket["id"])

        return {
            "action_id": action.id,
            "action_status": action.status,
            "ticket": ticket,
        }
    except Exception:
        db.rollback()
        raise
