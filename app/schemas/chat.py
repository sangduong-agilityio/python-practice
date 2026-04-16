from datetime import datetime

from pydantic import BaseModel, Field


class ChatSend(BaseModel):
    """Payload a client sends over the websocket."""

    recipient_id: int
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatEvent(BaseModel):
    """Envelope sent over websocket."""

    type: str = Field(default="chat.message")
    data: ChatMessageResponse

