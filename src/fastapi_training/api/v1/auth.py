from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.user import UserCreate, UserResponse
from ...schemas.auth import RefreshTokenRequest, LogoutRequest, LoginTokenResponse, TokenResponse
from ..deps import get_db
from ...services.user_service import create_user
from ...services import auth_service
from ...services.email_service import send_welcome_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    user = await create_user(db, user_in)
    
    # Send welcome email via Celery Redis Worker
    send_welcome_email.delay(user.email)
    
    return user


@router.post("/login", response_model=LoginTokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> LoginTokenResponse:
    """
    Authenticate with email + password.
    Returns an access token (short-lived) and a refresh token (stored in DB).
    """
    return await auth_service.login(db, email=form_data.username, password=form_data.password)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """
    Exchange a valid, non-revoked refresh token for a new access token.
    The refresh token itself is NOT rotated (simple approach).
    """
    return await auth_service.refresh(db, refresh_token_str=body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)) -> None:
    """
    Revoke a refresh token so it can no longer be used to obtain access tokens.
    This is the server-side logout — clients should also discard their stored tokens.
    """
    await auth_service.logout(db, refresh_token_str=body.refresh_token)
