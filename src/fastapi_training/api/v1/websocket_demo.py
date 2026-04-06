from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter(prefix="/ws", tags=["Notifications"])

class NotificationManager:
    """Manages active WebSocket connections for real-time notifications."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send a notification to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Handle cases where connection might have closed unexpectedly
                pass

# Global instance to be used across the application
notification_manager = NotificationManager()

@router.websocket("/notifications/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await notification_manager.connect(websocket)
    try:
        # Welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to notification server as Client #{client_id}"
        })
        
        while True:
            # Keep the connection alive
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
