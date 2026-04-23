from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.dependencies import CurrentUser, DbSession
from app.core.security import decode_access_token
from app.core.websocket import manager
from app.schemas.chat import ChatEvent, ChatMessageResponse, ChatSend
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _extract_bearer_from_ws(websocket: WebSocket) -> str | None:
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


@router.get(
    "/threads/{other_user_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def list_thread_messages(
    other_user_id: int,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    before_id: int | None = Query(default=None, ge=1),
) -> list[ChatMessageResponse]:
    """List chat messages between the current user and another user."""
    msgs = await ChatService(db).list_thread(
        current_user_id=current_user.id,
        other_user_id=other_user_id,
        limit=limit,
        before_id=before_id,
    )
    return msgs


@router.websocket("/ws")
async def chat_ws(
    websocket: WebSocket,
    db: DbSession,
    token: str | None = Query(default=None),
):
    """Realtime chat websocket.

    Auth:
    - Prefer `Authorization: Bearer <jwt>`
    - Also accepts `?token=` for easier local testing.

    Client sends JSON:
      { "recipient_id": 2, "content": "hi" }

    Server pushes JSON:
      { "type": "chat.message", "data": { ...ChatMessageResponse } }
    """
    if token is None:
        token = _extract_bearer_from_ws(websocket)
    if not token:
        await websocket.close(code=1008)
        return

    user_id_str = decode_access_token(token)
    if not user_id_str:
        await websocket.close(code=1008)
        return

    try:
        user_id = int(user_id_str)
    except ValueError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            payload = ChatSend.model_validate(data)
            msg = await ChatService(db).send_message(
                sender_id=user_id,
                recipient_id=payload.recipient_id,
                content=payload.content,
            )
            # No need to send here; ChatService already broadcasts to sender+recipient.
            _ = ChatEvent(data=ChatMessageResponse.model_validate(msg))
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        # Close on protocol errors (bad JSON, validation, etc.)
        manager.disconnect(websocket, user_id)
        await websocket.close(code=1003)

