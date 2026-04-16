import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException, ResourceNotFoundException
from app.core.websocket import manager
from app.models.chat_message import ChatMessage
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository

log = structlog.get_logger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatRepository(db)
        self.user_repo = UserRepository(db)

    async def send_message(
        self,
        *,
        sender_id: int,
        recipient_id: int,
        content: str,
    ) -> ChatMessage:
        if sender_id == recipient_id:
            raise PermissionDeniedException("Cannot message yourself")

        recipient = await self.user_repo.get_by_id(recipient_id)
        if recipient is None:
            raise ResourceNotFoundException("User")

        msg = await self.repo.create(
            ChatMessage(sender_id=sender_id, recipient_id=recipient_id, content=content)
        )

        payload = {
            "type": "chat.message",
            "data": {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "recipient_id": msg.recipient_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            },
        }

        # Push to recipient and sender (so sender can update UI without waiting for REST).
        await manager.send_personal_message(payload, recipient_id)
        await manager.send_personal_message(payload, sender_id)

        log.info(
            "chat.message_sent",
            message_id=msg.id,
            sender_id=sender_id,
            recipient_id=recipient_id,
        )
        return msg

    async def list_thread(
        self,
        *,
        current_user_id: int,
        other_user_id: int,
        limit: int = 50,
        before_id: int | None = None,
    ) -> list[ChatMessage]:
        # Ensure other user exists (more helpful than returning empty list).
        other = await self.user_repo.get_by_id(other_user_id)
        if other is None:
            raise ResourceNotFoundException("User")

        return await self.repo.list_between_users(
            current_user_id, other_user_id, limit=limit, before_id=before_id
        )

