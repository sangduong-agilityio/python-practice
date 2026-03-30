"""
CRUD operations for RefreshToken model.
These functions handle only DB interactions — no business logic here.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.refresh_token import RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    *,
    token: str,
    user_id: int,
    expires_at: datetime,
) -> RefreshToken:
    """Persist a new refresh token record for a user."""
    db_token = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def get_refresh_token(
    db: AsyncSession, *, token: str
) -> Optional[RefreshToken]:
    """Look up a refresh token record by its raw token string."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    return result.scalars().first()


async def revoke_refresh_token(db: AsyncSession, *, token_record: RefreshToken) -> RefreshToken:
    """Mark a single refresh token as revoked."""
    token_record.is_revoked = True
    db.add(token_record)
    await db.commit()
    await db.refresh(token_record)
    return token_record


async def revoke_all_by_user(db: AsyncSession, *, user_id: int) -> None:
    """ 
    Revoke ALL active refresh tokens for a user.
    Useful when the user changes their password or requests a global logout.
    """
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  
        )
    )
    tokens = result.scalars().all()
    for t in tokens:
        t.is_revoked = True
        db.add(t)
    await db.commit()
