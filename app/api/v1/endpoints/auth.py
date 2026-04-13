"""
Auth endpoints -- register, login, refresh, and logout.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUser, DbSession, RawToken
from app.schemas.auth import LogoutRequest, RefreshRequest, Token
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
    """Authenticate with email and password, return an access token and refresh token.

    The refresh token is an opaque random string whose SHA-256 hash is stored
    in the database.  Device info and IP are captured for session management.
    """
    return await UserService(db).login(
        form_data.username, form_data.password, request=request
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh(request: Request, body: RefreshRequest, db: DbSession) -> Token:
    """Exchange a valid refresh token for a new access + refresh token pair.

    The old refresh token is immediately invalidated (rotation).  If the same
    refresh token is presented twice, all sessions for the user are revoked
    (reuse / theft detection).
    """
    return await UserService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    token: RawToken,
    current_user: CurrentUser,
    body: LogoutRequest,
    db: DbSession,
) -> None:
    """Revoke the current session.

    * The Bearer access token is blacklisted in Redis for its remaining lifetime.
    * If ``refresh_token`` is included in the request body, the corresponding
      database session row is also marked revoked -- strongly recommended so the
      client cannot silently obtain a new access token after logging out.

    Returns **204 No Content** on success.
    """
    await UserService(db).logout(
        access_token=token,
        raw_refresh_token=body.refresh_token,
    )
