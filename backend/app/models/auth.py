"""Pydantic models for authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    """Public user representation."""

    id: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    """Registration request body."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    """JSON login request body."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Login/token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: Optional[str] = None
    exp: Optional[datetime] = None
