"""
Auth endpoints -- register and login.

Route handlers do three things only: validate input (Pydantic),
call the service, return the result. No business logic lives here.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import DbSession
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> UserResponse:
    user = await user_service.register(db, data, background_tasks)
    return user 


@router.post("/login", response_model=Token)
async def login(
    # OAuth2PasswordRequestForm reads form data (not JSON).
    # The field is called "username" per the spec, but we use it as email.
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    return await user_service.login(db, form_data.username, form_data.password)
