from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class RefreshToken(SQLModel, table=True):
    """
    Persisted refresh tokens.
    Storing tokens in DB allows us to revoke them individually
    """

    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # The SHA-256 hashed JWT string — used as the lookup key on /refresh and /logout.
    # We do NOT store the raw token string in the DB for security reasons.
    token: str = Field(unique=True, index=True)

    user_id: int = Field(foreign_key="users.id", nullable=False)

    expires_at: datetime = Field(nullable=False)

    # When True this token is no longer accepted on /refresh
    is_revoked: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=datetime.now
    )

    # Relationship (back-reference only; User does not need a forward ref here)
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")
