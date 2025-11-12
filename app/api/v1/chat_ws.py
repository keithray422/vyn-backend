from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.db.database import get_db
from app.models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession
import json
import datetime

router = APIRouter()

# Keep track of connected users
active_connections = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"✅ User {user_id} connected.")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            sender_id = message_data["sender_id"]
            receiver_id = message_data["receiver_id"]
            content = message_data["content"]

            # Save message to DB
            new_message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                timestamp=datetime.datetime.utcnow(),
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)

            # Send message to receiver (if online)
            if receiver_id in active_connections:
                await active_connections[receiver_id].send_text(json.dumps({
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "content": content,
                    "timestamp": new_message.timestamp.isoformat(),
                }))

            # Echo to sender for confirmation
            await websocket.send_text(json.dumps({
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": content,
                "timestamp": new_message.timestamp.isoformat(),
            }))

    except WebSocketDisconnect:
        print(f"❌ User {user_id} disconnected.")
        del active_connections[user_id]
