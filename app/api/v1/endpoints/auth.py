"""
Auth endpoints -- register and login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import DbSession
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, data: UserCreate, db: DbSession) -> UserResponse:
    """Register a new user account."""
    user = await UserService(db).register(data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    """Authenticate with email and password, return a JWT access token."""
    return await UserService(db).login(form_data.username, form_data.password)
