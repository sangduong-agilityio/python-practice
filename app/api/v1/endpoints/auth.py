"""
app/api/v1/endpoints/auth.py
-----------------------------
Authentication endpoints: register and login.

Route handlers in this project follow one rule:
  1. Validate input (Pydantic does this automatically via the schema).
  2. Call the service.
  3. Return the response.

No business logic lives in route handlers — that belongs in services.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.user import Token, UserCreate, UserOut
from app.services.email_service import send_welcome_email
from app.services.user_service import UserService

# APIRouter groups related endpoints together.
# The prefix and tags are applied when this router is mounted in router.py.
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> UserOut:
    """
    Create a new user account.

    - **email**: Must be a valid, unique email address.
    - **username**: 3-50 characters, letters/digits/underscores only.
    - **password**: Minimum 8 characters.

    Returns the created user profile (no password in response).
    """
    service = UserService(db)
    user = await service.register(data)

    # Schedule the welcome email to send AFTER the response is returned.
    # The user doesn't wait for the email — great for UX.
    background_tasks.add_task(send_welcome_email, user.email, user.username)

    return user  # type: ignore[return-value]


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
async def login(
    # OAuth2PasswordRequestForm parses multipart/form-data with two fields:
    #   - username : we treat this as the user's email address
    #   - password : plain-text password (hashed inside the service)
    #
    # Using Depends() tells FastAPI to inject and parse the form automatically.
    # This is the standard OAuth2 "password" grant flow, which also makes the
    # /docs UI show a working "Authorize" button out of the box.
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    """
    Authenticate with email and password (OAuth2 Password Grant).

    **Form fields** (send as `application/x-www-form-urlencoded`):
    - `username` — your registered email address
    - `password` — your account password

    Returns a JWT Bearer token. Include this in all subsequent requests:
    `Authorization: Bearer <your_token>`
    """
    service = UserService(db)
    # form.username holds the email (OAuth2 spec uses "username" as the field name)
    return await service.login(email=form.username, password=form.password)
