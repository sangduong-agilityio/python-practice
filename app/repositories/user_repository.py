"""
User repository -- raw database operations only.

Nothing in this file raises HTTPException or contains business rules.
If a user is not found, return None and let the service layer decide
whether that is an error or just an empty result.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Raw database operations for users."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch a user by primary key, or ``None`` if it has no match."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address (case-sensitive), or ``None`` on miss."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by unique username, or ``None`` if not found."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new ``User`` instance, commit the transaction, and return the
        refreshed object with all server-generated fields (``id``, ``created_at``).
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: dict) -> User:
        """Apply a partial update to a ``User`` and flush the changes."""
        for field, value in data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user
