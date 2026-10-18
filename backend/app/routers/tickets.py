from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.db.database import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import TicketPage, TicketResponse, TicketUpdate
from app.models.user import User
from app.services.audit import record_event

router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["tickets"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=TicketPage)
def list_tickets(
    status: str | None = Query(default=None, pattern="^(open|in_progress|resolved|closed)$"),
    priority: str | None = Query(default=None, pattern="^(low|medium|high|urgent)$"),
    customer_id: int | None = Query(default=None, ge=1),
    q: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = []
    if status:
        filters.append(Ticket.status == status)
    if priority:
        filters.append(Ticket.priority == priority)
    if customer_id:
        filters.append(Ticket.customer_id == customer_id)
    if q and q.strip():
        filters.append(Ticket.title.ilike(f"%{q.strip()}%"))
    total = db.scalar(select(func.count(Ticket.id)).where(*filters)) or 0
    items = db.execute(select(Ticket).where(*filters).order_by(Ticket.created_at.desc(), Ticket.id.desc()).offset(offset).limit(limit)).scalars().all()
    return TicketPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    request: TicketUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("admin", "agent")),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    before = {"status": ticket.status, "priority": ticket.priority}
    if request.status is not None:
        ticket.status = request.status
    if request.priority is not None:
        ticket.priority = request.priority
    db.commit()
    db.refresh(ticket)
    record_event(db, actor, "ticket.updated", "ticket", ticket.id, {"before": before, "after": {"status": ticket.status, "priority": ticket.priority}})
    return ticket
