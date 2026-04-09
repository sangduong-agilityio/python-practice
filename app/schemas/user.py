"""
User request/response schemas.

The naming convention used throughout this codebase:
  Base   -- shared fields
  Create -- fields required when POSTing a new resource
  Update -- all optional, for partial PUT/PATCH
  Response -- what goes back to the caller (never the password hash)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Fields shared between create and response schemas."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    # from_attributes lets Pydantic read values from SQLAlchemy ORM objects
    # instead of requiring a plain dict.
    model_config = {"from_attributes": True}
