from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, login, require_auth, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, PasswordChange, SessionResponse
from app.services.audit import record_event

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def create_session(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        token = login(request.username, request.password, db)
    except HTTPException as exc:
        if exc.status_code == 401:
            record_event(db, None, "auth.login_failed", "user", None, actor_username=request.username[:128])
        raise
    user = db.execute(select(User).where(User.username == request.username)).scalar_one()
    record_event(db, user, "auth.login_succeeded", "user", user.id)
    response.set_cookie("support_session", token, max_age=settings.auth_token_ttl_minutes * 60, httponly=True, secure=settings.auth_cookie_secure, samesite="lax", path="/api/v1")
    return LoginResponse()


@router.get("/session", response_model=SessionResponse)
def get_session(user: User = Depends(require_auth)):
    return SessionResponse(username=user.username, role=user.role)


@router.post("/password")
def change_password(
    request: PasswordChange,
    response: Response,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.password_hash = hash_password(request.new_password)
    user.session_version += 1
    db.commit()
    record_event(db, user, "auth.password_changed", "user", user.id)
    response.set_cookie("support_session", create_access_token(user), max_age=settings.auth_token_ttl_minutes * 60, httponly=True, secure=settings.auth_cookie_secure, samesite="lax", path="/api/v1")
    return {"changed": True}


@router.post("/logout")
def logout(response: Response, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    record_event(db, user, "auth.logout", "user", user.id)
    response.delete_cookie("support_session", path="/api/v1", httponly=True, secure=settings.auth_cookie_secure, samesite="lax")
    return {"authenticated": False}
