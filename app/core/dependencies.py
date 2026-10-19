"""
app/core/dependencies.py
------------------------
FastAPI dependency functions shared across route handlers.

FastAPI's dependency injection system works like this:
  - You define a function that yields or returns a value.
  - Route handlers declare it as a parameter using `Depends(your_function)`.
  - FastAPI calls the function automatically and passes the result in.

This file provides two core dependencies:
  1. `get_db`           — yields a database session, always closes it after the request.
  2. `get_current_user` — reads + validates the JWT, returns the User ORM object.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# OAuth2 Scheme
# ---------------------------------------------------------------------------
# This tells FastAPI (and Swagger UI) that protected endpoints need a Bearer token.
# `tokenUrl` is the endpoint where clients obtain a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Database Session Dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    Yield a database session for a single request, then close it.

    Using `yield` makes this a "context manager dependency":
    - FastAPI opens the session before the route handler runs.
    - FastAPI closes it after the response is sent (even if an error occurred).
    This guarantees we never leak database connections.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()   # Commit if everything went fine
        except Exception:
            await session.rollback() # Roll back on any unhandled error
            raise


# ---------------------------------------------------------------------------
# Current User Dependency
# ---------------------------------------------------------------------------
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Extract and validate the JWT from the request header, then load the user.

    Args:
        token: The Bearer token from the `Authorization` header (auto-extracted).
        db   : Database session (auto-injected).

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: If the token is missing, invalid, expired, or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # RFC 6750 standard header
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # "sub" (subject) is the standard JWT claim we use to store user_id
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    user = await UserRepository(db).get_by_id(int(user_id_str))
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Thin wrapper around get_current_user — kept for readability in route signatures.
    Can be extended later (e.g., email verification check).
    """
    return current_user


# ---------------------------------------------------------------------------
# Type aliases for cleaner route signatures
# ---------------------------------------------------------------------------
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
