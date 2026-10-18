"""Database-backed workspace users and signed, revocable sessions."""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n, r, p = 32768, 8, 1
    digest = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, maxmem=128 * 1024 * 1024)
    return f"scrypt${n}${r}${p}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$", 5)
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(digest_hex)),
            maxmem=128 * 1024 * 1024,
        )
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _ensure_auth_configured() -> None:
    if not settings.auth_username or len(settings.auth_password) < 12 or len(settings.auth_secret_key) < 32:
        raise HTTPException(status_code=503, detail="Authentication needs a username, a 12-character password, and a 32-character signing secret.")


def ensure_bootstrap_admin(db: Session) -> None:
    """Create the first admin from environment configuration once, if needed."""
    if db.execute(select(User.id).limit(1)).first() is not None:
        return
    _ensure_auth_configured()
    db.add(User(
        username=settings.auth_username,
        password_hash=hash_password(settings.auth_password),
        role="admin",
        is_active=True,
    ))
    try:
        db.commit()
    except IntegrityError:
        # Another first-login request may have bootstrapped concurrently.
        db.rollback()


def create_access_token(user: User) -> str:
    _ensure_auth_configured()
    payload = _b64(json.dumps({
        "uid": user.id,
        "sub": user.username,
        "ver": getattr(user, "session_version", 0),
        "exp": int(time.time()) + settings.auth_token_ttl_minutes * 60,
    }, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.auth_secret_key.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def require_auth(
    session: str | None = Cookie(default=None, alias="support_session"),
    db: Session = Depends(get_db),
) -> User:
    _ensure_auth_configured()
    if session is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        payload, signature = session.split(".", 1)
        expected = _b64(hmac.new(settings.auth_secret_key.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data.get("exp", 0)) <= int(time.time()):
            raise ValueError("Expired token")
        user = db.get(User, int(data["uid"]))
        if user is None or not user.is_active or user.username != data.get("sub") or int(data.get("ver", -1)) != getattr(user, "session_version", 0):
            raise ValueError("Inactive or missing user")
        return user
    except (ValueError, TypeError, KeyError, AttributeError, binascii.Error, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired session.") from None


def require_role(*roles: str) -> Callable:
    def role_dependency(user: User = Depends(require_auth)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Your account does not have permission for this operation.")
        return user
    return role_dependency


def login(username: str, password: str, db: Session) -> str:
    _ensure_auth_configured()
    ensure_bootstrap_admin(db)
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    return create_access_token(user)
