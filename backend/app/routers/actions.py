from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.action import Action
from app.schemas.action import ActionProposal, ActionRecordResponse
from app.services.action_service import (
    approve_action,
    reject_action,
    save_action_proposal,
)
from app.services.action_executor import execute_action
from app.core.security import require_auth, require_role
from app.services.audit import record_event

router = APIRouter(
    prefix="/api/v1/actions",
    tags=["actions"],
    dependencies=[Depends(require_auth)],
)

@router.post("", response_model=ActionRecordResponse, status_code=201)
def create_action_proposal(
    proposal: ActionProposal,
    db: Session = Depends(get_db),
    actor=Depends(require_role("admin", "agent")),
):
    try:
        action = save_action_proposal(db=db, proposal=proposal)
        record_event(db, actor, "action.proposed", "action", action.id, {"action_type": action.action_type, "customer_id": action.customer_id})
        return action
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("", response_model=list[ActionRecordResponse])
def list_action_proposals(
    status: str | None = Query(default=None, description="Filter by status."),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    statement = select(Action).order_by(Action.created_at.desc()).limit(limit)
    if status is not None:
        statement = statement.where(Action.status == status)
    return list(db.execute(statement).scalars().all())

@router.get("/{action_id}", response_model=ActionRecordResponse)
def get_action_proposal(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = db.get(Action, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found.")
    return action

@router.post(
    "/{action_id}/approve",
    response_model=ActionRecordResponse,
)
def approve_action_endpoint(
    action_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_role("admin", "agent")),
):
    try:
        action = approve_action(db=db, action_id=action_id)
        record_event(db, actor, "action.approved", "action", action.id)
        return action
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.post(
    "/{action_id}/reject",
    response_model=ActionRecordResponse,
)
def reject_action_endpoint(
    action_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_role("admin", "agent")),
):
    try:
        action = reject_action(db=db, action_id=action_id)
        record_event(db, actor, "action.rejected", "action", action.id)
        return action
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    
@router.post("/{action_id}/execute")
def execute_action_endpoint(
    action_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_role("admin", "agent")),
):
    try:
        result = execute_action(db=db, action_id=action_id)
        record_event(db, actor, "action.executed", "action", action_id, {"ticket_id": result["ticket"]["id"]})
        return result
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Action execution failed.",
        ) from exc
