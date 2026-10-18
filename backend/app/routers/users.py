from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate, WorkspaceUser
from app.services.audit import record_event

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[WorkspaceUser])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return db.execute(select(User).order_by(User.username)).scalars().all()


@router.post("", response_model=WorkspaceUser, status_code=201)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    user = User(username=request.username, password_hash=hash_password(request.password), role=request.role, is_active=True)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That username is already in use.") from exc
    record_event(db, admin, "user.created", "user", user.id, {"username": user.username, "role": user.role})
    return user


@router.patch("/{user_id}", response_model=WorkspaceUser)
def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if request.role is None and request.is_active is None and request.password is None:
        raise HTTPException(status_code=422, detail="Provide an account change.")
    old = {"role": user.role, "is_active": user.is_active}
    next_role = request.role if request.role is not None else user.role
    next_active = request.is_active if request.is_active is not None else user.is_active
    if user.role == "admin" and user.is_active and (next_role != "admin" or not next_active):
        other_admins = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True), User.id != user.id)) or 0
        if other_admins == 0:
            raise HTTPException(status_code=409, detail="The last active administrator cannot be demoted or disabled.")
    user.role = next_role
    user.is_active = next_active
    if request.password is not None:
        user.password_hash = hash_password(request.password)
        user.session_version += 1
    db.commit()
    db.refresh(user)
    record_event(db, admin, "user.updated", "user", user.id, {"before": old, "after": {"role": user.role, "is_active": user.is_active}, "password_reset": request.password is not None})
    return user
