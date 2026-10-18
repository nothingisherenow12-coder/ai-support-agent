from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    authenticated: bool = True


class SessionResponse(BaseModel):
    username: str
    role: Literal["admin", "agent", "viewer"]


class WorkspaceUser(BaseModel):
    id: int
    username: str
    role: Literal["admin", "agent", "viewer"]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=256)
    role: Literal["admin", "agent", "viewer"] = "agent"


class UserUpdate(BaseModel):
    role: Literal["admin", "agent", "viewer"] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
