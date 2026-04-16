from fastapi import WebSocket
import structlog

log = structlog.get_logger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    def __init__(self):
        # Maps user_id to a list of active WebSocket connections
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a JSON payload to all active connections for a specific user."""
        if user_id not in self.active_connections:
            return

        stale: list[WebSocket] = []
        for connection in list(self.active_connections[user_id]):
            try:
                await connection.send_json(message)
            except Exception as exc:
                # Client disconnected unexpectedly or network error: mark stale.
                stale.append(connection)
                log.info("ws_send_failed", user_id=user_id, error=str(exc))

        for connection in stale:
            self.disconnect(connection, user_id)

# Global instance to be used across the app
manager = ConnectionManager()
