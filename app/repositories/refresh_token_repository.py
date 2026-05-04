"""
RefreshToken repository -- raw database operations only.

Nothing in this file raises HTTPException or contains business rules.
If a token is not found, return None and let the service layer decide
what that means in context (401, etc.).
"""

from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Raw database operations for refresh tokens."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, token: RefreshToken) -> RefreshToken:
        """Persist a new RefreshToken row and return it with server-generated fields."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch a refresh token by its SHA-256 hash, or None on miss."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: RefreshToken) -> None:
        """Stamp the token with the current UTC time to record it has been rotated.

        A non-NULL ``used_at`` on an *incoming* request is a reuse signal:
        the token was already rotated and someone is replaying the old value.
        """
        token.used_at = datetime.now(UTC)
        await self.db.flush()

    async def revoke(self, token: RefreshToken) -> None:
        """Mark a single refresh token as revoked (e.g. targeted logout)."""
        token.is_revoked = True
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        """Revoke every active refresh token belonging to a user.

        Called when token reuse is detected to invalidate all sessions
        in case an attacker has already rotated the stolen token.
        """
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        await self.db.flush()
