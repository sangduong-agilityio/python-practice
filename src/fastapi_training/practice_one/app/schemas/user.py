from ..dependencies.auth import get_current_user
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
