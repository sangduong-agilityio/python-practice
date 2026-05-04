from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, msg: ChatMessage) -> ChatMessage:
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def list_between_users(
        self,
        user_a_id: int,
        user_b_id: int,
        *,
        limit: int = 50,
        before_id: int | None = None,
    ) -> list[ChatMessage]:
        stmt = select(ChatMessage).where(
            or_(
                (ChatMessage.sender_id == user_a_id)
                & (ChatMessage.recipient_id == user_b_id),
                (ChatMessage.sender_id == user_b_id)
                & (ChatMessage.recipient_id == user_a_id),
            )
        )

        if before_id is not None:
            stmt = stmt.where(ChatMessage.id < before_id)

        stmt = stmt.order_by(ChatMessage.id.desc()).limit(limit)
        result = await self.db.execute(stmt)
        # Return chronological order for FE convenience.
        return list(reversed(list(result.scalars().all())))

