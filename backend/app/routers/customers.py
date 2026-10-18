from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerPage, CustomerResponse
from app.models.ticket import Ticket
from app.schemas.ticket import TicketPage, TicketResponse
from app.core.security import require_auth, require_role
from app.models.user import User as WorkspaceUser
from app.services.audit import record_event

router=APIRouter(
    prefix="/api/v1/customers",
    tags=["customers"],
    dependencies=[Depends(require_auth)],
)
@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
    actor: WorkspaceUser = Depends(require_role("admin", "agent")),
):
    customer = Customer(
        name=request.name.strip(),
        email=request.email.strip().lower(),
        company=request.company.strip() if request.company and request.company.strip() else None,
    )
    db.add(customer)
    try:
        db.commit()
        db.refresh(customer)
        record_event(db, actor, "customer.created", "customer", customer.id, {"email": customer.email})
        return customer
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A customer with this email already exists.") from exc


@router.get("", response_model=CustomerPage)
def list_customers(
    q: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = []
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters.append(or_(Customer.name.ilike(term), Customer.email.ilike(term), Customer.company.ilike(term)))
    total = db.scalar(select(func.count(Customer.id)).where(*filters)) or 0
    items = db.execute(select(Customer).where(*filters).order_by(Customer.name, Customer.id).offset(offset).limit(limit)).scalars().all()
    return CustomerPage(items=items, total=total, limit=limit, offset=offset)

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id:int,
    db:Session=Depends(get_db),
):
    customer=(
        db.query(Customer).filter(Customer.id==customer_id).first())
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    return customer
@router.get(
    "/{customer_id}/tickets",
    response_model=TicketPage
)
def get_customer_tickets(
    customer_id: int,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    customer=(
        db.query(Customer).filter(Customer.id==customer_id).first()
    )

    if customer is None:
        raise HTTPException(status_code=404,detail="Customer not found")

    total = db.scalar(select(func.count(Ticket.id)).where(Ticket.customer_id == customer_id)) or 0
    tickets = db.execute(select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc(), Ticket.id.desc()).offset(offset).limit(limit)).scalars().all()
    return TicketPage(items=tickets, total=total, limit=limit, offset=offset)
