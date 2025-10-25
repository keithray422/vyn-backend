from typing import Dict, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # map user_id (int) -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        # Accept then store
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message: str, user_id: int) -> bool:
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_text(message)
                return True
            except Exception:
                # connection broken
                self.disconnect(user_id)
        return False

# singleton instance used across the app
manager = ConnectionManager()
