from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow_naive
from app.models.audit_event import AuditEvent
from app.models.user import User


def record_event(
    db: Session,
    actor: User | None,
    event_type: str,
    entity_type: str,
    entity_id: int | str | None,
    details: dict[str, Any] | None = None,
    actor_username: str | None = None,
) -> None:
    db.add(AuditEvent(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else (actor_username or "system"),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details,
        created_at=utcnow_naive(),
    ))
    db.commit()


def recent_events(db: Session, limit: int = 100) -> list[AuditEvent]:
    return list(db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit)).scalars().all())
