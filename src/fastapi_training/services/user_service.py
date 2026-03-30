"""
User service — business logic layer.
All database operations are delegated to crud.user.
"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password, verify_password
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..crud import user as user_crud


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Register a new user. Raises 400 if email is already taken."""
    if await user_crud.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed = hash_password(user_in.password)
    return await user_crud.create_user_db(db, email=user_in.email, hashed_password=hashed)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Look up a user by email."""
    return await user_crud.get_user_by_email(db, email=email)


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Verify credentials and return the user, or None on failure."""
    user = await user_crud.get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user(
    db: AsyncSession, user_id: int, user_update: UserUpdate
) -> Optional[User]:
    """Apply partial updates to a user. Raises 400 if new email is already taken."""
    db_user = await user_crud.get_user(db, user_id)
    if not db_user:
        return None

    update_fields: dict = {}

    if user_update.email is not None:
        existing = await user_crud.get_user_by_email(db, email=user_update.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        update_fields["email"] = user_update.email

    if user_update.password is not None:
        update_fields["hashed_password"] = hash_password(user_update.password)

    if update_fields:
        return await user_crud.update_user_db(db, db_user, update_fields)
    return db_user
