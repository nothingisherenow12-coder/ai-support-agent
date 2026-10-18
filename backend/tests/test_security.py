from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import security


class FakeResult:
    def __init__(self, user=None):
        self.user = user

    def first(self):
        return (1,)  # The workspace has already been bootstrapped.

    def scalar_one_or_none(self):
        return self.user


class FakeDB:
    def __init__(self, user):
        self.user = user
        self.lookups = 0

    def execute(self, _statement):
        self.lookups += 1
        return FakeResult(self.user)

    def get(self, _model, user_id):
        return self.user if self.user.id == user_id else None


def configure_auth(monkeypatch):
    monkeypatch.setattr(security.settings, "auth_username", "operator")
    monkeypatch.setattr(security.settings, "auth_password", "test-password")
    monkeypatch.setattr(security.settings, "auth_secret_key", "s" * 40)
    monkeypatch.setattr(security.settings, "auth_token_ttl_minutes", 5)
    password_hash = security.hash_password("test-password")
    return SimpleNamespace(id=1, username="operator", password_hash=password_hash, role="admin", is_active=True)


def test_login_and_session_validation(monkeypatch):
    user = configure_auth(monkeypatch)
    db = FakeDB(user)
    token = security.login("operator", "test-password", db)
    assert security.require_auth(token, db) is user


def test_wrong_password_is_rejected(monkeypatch):
    user = configure_auth(monkeypatch)
    with pytest.raises(HTTPException) as error:
        security.login("operator", "wrong-password", FakeDB(user))
    assert error.value.status_code == 401


def test_tampered_session_is_rejected(monkeypatch):
    user = configure_auth(monkeypatch)
    token = security.login("operator", "test-password", FakeDB(user))
    with pytest.raises(HTTPException) as error:
        security.require_auth(token + "x", FakeDB(user))
    assert error.value.status_code == 401


def test_inactive_user_session_is_rejected(monkeypatch):
    user = configure_auth(monkeypatch)
    token = security.login("operator", "test-password", FakeDB(user))
    user.is_active = False
    with pytest.raises(HTTPException) as error:
        security.require_auth(token, FakeDB(user))
    assert error.value.status_code == 401


def test_password_change_version_revokes_existing_sessions(monkeypatch):
    user = configure_auth(monkeypatch)
    user.session_version = 0
    token = security.login("operator", "test-password", FakeDB(user))
    user.session_version += 1
    with pytest.raises(HTTPException) as error:
        security.require_auth(token, FakeDB(user))
    assert error.value.status_code == 401
