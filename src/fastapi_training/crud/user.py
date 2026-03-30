"""
CRUD operations for User model.
Pure database operations — no business logic.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Fetch a single user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Fetch a single user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user_db(db: AsyncSession, email: str, hashed_password: str) -> User:
    """Insert a new user record and return it."""
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_db(db: AsyncSession, db_user: User, update_fields: dict) -> User:
    """Apply a dict of field updates to an existing user and persist."""
    for key, value in update_fields.items():
        setattr(db_user, key, value)
    await db.commit()
    await db.refresh(db_user)
    return db_user
