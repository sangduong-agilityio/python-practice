"""
app/repositories/user_repository.py
------------------------------------
Database access layer for the User model.

The Repository pattern separates raw DB queries from business logic:
  - Repositories ONLY know about the database (SQLAlchemy sessions, models).
  - They do NOT raise HTTPException or know about FastAPI.
  - Services call repositories and decide what to do with the results.

This makes code easier to test (swap DB for a mock) and reason about.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """
    Encapsulates all SQL queries related to the User model.

    Args:
        db: An async SQLAlchemy session, injected via dependency.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Fetch a user by primary key.

        Returns:
            User object if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address (case-insensitive)."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, email: str, username: str, hashed_password: str) -> User:
        """
        Insert a new user row into the database.

        Args:
            email           : Normalized (lowercase) email address.
            username        : Normalized (lowercase) username.
            hashed_password : bcrypt hash of the plain password.

        Returns:
            The newly created User ORM object with its `id` populated.
        """
        user = User(
            email=email.lower(),
            username=username.lower(),
            hashed_password=hashed_password,
        )
        self.db.add(user)
        await self.db.flush()    # Write to DB without committing (gets the auto-generated id)
        await self.db.refresh(user)  # Reload from DB to populate server-set fields like created_at
        return user

    async def update(self, user: User, **kwargs) -> User:
        """
        Update arbitrary fields on an existing User.

        Args:
            user  : The User ORM object to update.
            **kwargs: Field names and new values, e.g. update(user, email="new@x.com")

        Returns:
            The updated User object.
        """
        for field, value in kwargs.items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user
