"""
Auth service — business logic for authentication.
Coordinates between CRUD, security helpers, and the caller (route handlers).
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_token,
    TokenError,
)
from ..models.user import User
from ..schemas.auth import LoginTokenResponse, TokenResponse
from ..crud import user as user_crud
from ..crud import refresh_token as rt_crud


async def login(db: AsyncSession, email: str, password: str) -> LoginTokenResponse:
    """
    Authenticate a user and create persisted tokens.

    Steps:
    Verify credentials
    Create access token (stateless JWT)
    Create refresh token (JWT)
    Hash refresh token and store it in the DB
    Return both tokens
    """
    # Verify credentials
    user = await user_crud.get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token (not stored in DB — validated by signature only)
    access_token = create_access_token(data={"sub": user.email})

    # Create refresh token
    refresh_token_str, expires_at = create_refresh_token(data={"sub": user.email})
    
    # Hash and persist it in DB
    hashed_rt = hash_token(refresh_token_str)
    await rt_crud.create_refresh_token(
        db,
        token=hashed_rt,
        user_id=user.id,
        expires_at=expires_at,
    )

    return LoginTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
    )


async def refresh(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """
    Issue a new access token if the refresh token is valid and not revoked.

    Validation order:
    JWT signature + expiry (via verify_token)
    Hash the provided token
    Token hash exists in DB
    Token is not revoked
    """
    # Validate JWT signature & expiry
    try:
        payload = verify_token(refresh_token_str)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Hash the token to look it up in DB
    hashed_rt = hash_token(refresh_token_str)
    token_record = await rt_crud.get_refresh_token(db, token=hashed_rt)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    # Check revocation status
    if token_record.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Extra safety: check DB-stored expiry (consistent with JWT exp)
    if token_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    email = payload.get("sub")
    new_access_token = create_access_token(data={"sub": email})
    return TokenResponse(access_token=new_access_token, token_type="bearer")


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    """
    Revoke a refresh token so it can no longer be used.
    If the token is not found, silently ignore (idempotent).
    """
    hashed_rt = hash_token(refresh_token_str)
    token_record = await rt_crud.get_refresh_token(db, token=hashed_rt)
    if token_record and not token_record.is_revoked:
        await rt_crud.revoke_refresh_token(db, token_record=token_record)

