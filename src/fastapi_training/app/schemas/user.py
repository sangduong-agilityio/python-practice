from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration.

    Validation rules:
    - email: Must be valid email format (checked by EmailStr)
    - password: At least 8 characters
    """
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity.

        Args:
            v: Password string

        Returns:
            Password if valid

        Raises:
            ValueError: If password is too short
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user info."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
