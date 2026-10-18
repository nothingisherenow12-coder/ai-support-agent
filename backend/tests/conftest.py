"""Keep API integration tests independent of deployment credentials."""
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import ensure_bootstrap_admin, hash_password, require_auth
from app.core.config import settings
from app.db.database import get_db
from app.main import app
from app.models.user import User


def test_operator(db: Session = Depends(get_db)) -> User:
    user = db.execute(select(User).where(User.username == settings.auth_username)).scalar_one_or_none()
    if user is None:
        # Preserve a workspace created by the earlier test suite, which seeded
        # a test-only admin before the configured bootstrap account existed.
        legacy_test_user = db.execute(select(User).where(User.username == "test-operator")).scalar_one_or_none()
        if legacy_test_user is not None:
            legacy_test_user.username = settings.auth_username
            legacy_test_user.password_hash = hash_password(settings.auth_password)
            legacy_test_user.role = "admin"
            legacy_test_user.is_active = True
            db.commit()
            db.refresh(legacy_test_user)
            user = legacy_test_user
        else:
            ensure_bootstrap_admin(db)
            user = db.execute(select(User).where(User.username == settings.auth_username)).scalar_one_or_none()
    if user is None:
        raise RuntimeError("Configured test workspace admin could not be initialized.")
    return user


app.dependency_overrides[require_auth] = test_operator
