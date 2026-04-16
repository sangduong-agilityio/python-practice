"""
ChatMessage model for realtime user-to-user chat.

Minimal schema:
- sender_id / recipient_id: integer user IDs
- content: message text

This is intentionally simple to support websocket demo and FE integration.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Keep a modest max size to avoid abusing websocket payloads.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} {self.sender_id}->{self.recipient_id}>"

