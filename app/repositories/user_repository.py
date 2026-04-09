"""
User repository -- raw database operations only.

Nothing in this file raises HTTPException or contains business rules.
If a user is not found, return None and let the service layer decide
whether that is an error or just an empty result.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetch a user by primary key, or ``None`` if the UUID has no match."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address (case-sensitive), or ``None`` on miss."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    """Fetch a user by unique username, or ``None`` if not found."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user: User) -> User:
    """Persist a new ``User`` instance, commit the transaction, and return the
    refreshed object with all server-generated fields (``id``, ``created_at``).
    """
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, data: dict) -> User:
    """Apply a partial update to a ``User`` and flush the changes.

    Args:
        user: The ORM instance to mutate. Must already be tracked by ``db``.
        data: A dict of field names to new values (typically the output of
              ``schema.model_dump(exclude_none=True)``).

    Returns:
        The refreshed ``User`` instance after the commit.
    """
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
