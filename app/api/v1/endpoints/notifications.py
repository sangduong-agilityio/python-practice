from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.core.websocket import manager

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(default=None)):
    """WebSocket endpoint for receiving real-time notifications.
    
    The client must provide a valid JWT access token as a query parameter
    `?token=...` to authenticate the connection.

    For non-browser clients we also accept an Authorization header:
    `Authorization: Bearer <token>`.
    """
    if token is None:
        auth = websocket.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

    if not token:
        await websocket.close(code=1008)
        return

    user_id_str = decode_access_token(token)
    if not user_id_str:
        # Invalid or expired token
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
            # The server waits for incoming messages to keep the connection alive
            # In a push-notification system, we usually ignore client messages
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
