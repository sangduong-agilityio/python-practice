"""
FastAPI dependency functions.

get_db yields a session per request and closes it when the request ends,
whether it succeeded or raised an exception. get_current_user decodes the
JWT and loads the user from the database on every authenticated request.

The Annotated type aliases (DbSession, CurrentUser) keep route handler
signatures short without hiding what is actually being injected.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db():
    """Yield an async database session for the duration of a single request.

    The session is automatically closed (and any uncommitted transaction rolled
    back) when the request finishes, whether it succeeds or raises an exception.
    Inject this via ``DbSession`` rather than calling it directly.
    """
    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Resolve the Bearer token to an active ``User`` ORM object.

    Decodes the JWT, validates the ``sub`` claim is a well-formed UUID, and
    confirms the user still exists and is active. Raises ``HTTP 401`` for any
    token issue and ``HTTP 403`` if the account has been deactivated.

    Args:
        token: Raw Bearer token extracted from the ``Authorization`` header by
               ``OAuth2PasswordBearer``.
        db: Async database session injected by ``get_db``.

    Returns:
        The authenticated, active ``User`` instance.

    Raises:
        HTTPException 401: Token is missing, expired, tampered, or the subject
                           UUID does not exist in the database.
        HTTPException 403: The account matched the token but is marked inactive.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id_str = decode_access_token(token)
    if user_id_str is None:
        raise unauthorized

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise unauthorized

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise unauthorized

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
