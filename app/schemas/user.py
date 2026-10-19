"""
app/schemas/user.py
-------------------
Pydantic schemas for User-related API input/output.

Pydantic schemas serve two purposes:
  1. REQUEST schemas validate and parse incoming JSON from the client.
  2. RESPONSE schemas control exactly what fields are sent back to the client.
     (We never accidentally expose hashed_password this way.)

The pattern used here is:
  UserBase   — shared fields
  UserCreate — extends Base, adds password field (write-only)
  UserUpdate — all fields optional (PATCH-style updates)
  UserOut    — response schema, no sensitive fields
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Fields shared between create and response schemas."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """
    Schema for POST /auth/register.
    Password must be at least 8 characters — enforced by the validator.
    """
    password: str = Field(min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Usernames may only contain letters, digits, and underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only letters, digits, and underscores")
        return v.lower()  # Normalize to lowercase


class UserUpdate(BaseModel):
    """
    Schema for PUT /users/me.
    All fields are optional — client sends only what they want to change.
    """
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=50)
    password: str | None = Field(default=None, min_length=8, max_length=100)


class UserOut(UserBase):
    """
    Response schema — safe to return to the client.
    `from_attributes=True` allows building this from a SQLAlchemy ORM object.
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Response schema for POST /auth/login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal schema — the decoded payload stored inside a JWT."""
    user_id: int | None = None
