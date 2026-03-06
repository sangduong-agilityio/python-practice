from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: EmailStr


class UserUpdate(BaseModel):
    """Schema for updating user info."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
