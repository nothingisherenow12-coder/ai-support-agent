from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditEventResponse
from app.services.audit import recent_events

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("", response_model=list[AuditEventResponse])
def list_audit_events(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _admin: User = Depends(require_role("admin"))):
    return recent_events(db, limit)
