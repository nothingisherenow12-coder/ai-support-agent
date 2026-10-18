from sqlalchemy.orm import Session
from sqlalchemy import select
import logging
from app.models.customer import Customer
from app.models.action import Action
from app.schemas.action import ActionProposal

logger = logging.getLogger(__name__)

def save_action_proposal(
    db: Session,
    proposal: ActionProposal,
) -> Action:
    if proposal.customer_id is not None:
        customer = db.get(Customer, proposal.customer_id)
        if customer is None:
            raise ValueError(
                f"Customer {proposal.customer_id} does not exist."
            )

    action = Action(
        action_type=proposal.action_type,
        customer_id=proposal.customer_id,
        title=proposal.title,
        description=proposal.description,
        reason=proposal.reason,
        status="proposed",
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    logger.info("action %s proposed: %s for customer %s", action.id, action.action_type, action.customer_id)

    return action

def _change_action_status(
    db: Session,
    action_id: int,
    new_status: str,
) -> Action:
    action = db.execute(
        select(Action)
        .where(Action.id == action_id)
        .with_for_update()
    ).scalar_one_or_none()

    if action is None:
        raise LookupError(f"Action {action_id} not found.")

    if action.status != "proposed":
        raise ValueError(
            f"Cannot change action from status '{action.status}'."
        )

    if new_status == "approved":
        if action.action_type == "create_ticket":
            if action.customer_id is None:
                raise ValueError(
                    "Cannot approve a ticket action without a customer ID."
                )

            customer = db.get(Customer, action.customer_id)

            if customer is None:
                raise ValueError(
                    f"Customer {action.customer_id} does not exist."
                )

    try:
        action.status = new_status
        db.commit()
        db.refresh(action)
        logger.info("action %s: %s", action.id, new_status)
        return action
    except Exception:
        db.rollback()
        raise

def approve_action(db: Session, action_id: int) -> Action:
    return _change_action_status(
        db=db,
        action_id=action_id,
        new_status="approved",
    )

def reject_action(db: Session, action_id: int) -> Action:
    return _change_action_status(
        db=db,
        action_id=action_id,
        new_status="rejected",
    )
