"""
RefreshToken model.

Stores SHA-256 hashes of opaque refresh tokens issued to clients.
The raw token is NEVER persisted -- only its hash, mirroring the
password-hashing pattern so a compromised database cannot be used
to impersonate any user.

"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key -- cascade delete keeps the table clean when a user is removed.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hex digest of the raw opaque token (64 chars).
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Optional audit / UX fields.
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Lifecycle flags.
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationship (back-populates declared on User).
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="refresh_tokens"
    )

    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id} revoked={self.is_revoked}>"
