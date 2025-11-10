from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.db.database import get_db
from app.models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

router = APIRouter()

active_connections = {}  # user_id -> WebSocket


async def save_message(db: AsyncSession, sender_id: int, receiver_id: int, content: str):
    msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"✅ User {user_id} connected.")

    try:
        while True:
            data = await websocket.receive_json()
            receiver_id = data.get("receiver_id")
            content = data.get("content")

            if not receiver_id or not content:
                await websocket.send_json({"error": "Missing receiver_id or content"})
                continue

            # Save the message
            message = await save_message(db, sender_id=user_id, receiver_id=receiver_id, content=content)

            # Deliver instantly if receiver is connected
            receiver_ws = active_connections.get(receiver_id)
            if receiver_ws:
                await receiver_ws.send_json({
                    "type": "message",
                    "from": user_id,
                    "content": content,
                    "timestamp": str(message.timestamp)
                })

            # Confirm to sender
            await websocket.send_json({
                "type": "sent",
                "to": receiver_id,
                "content": content,
                "timestamp": str(message.timestamp)
            })

    except WebSocketDisconnect:
        print(f"❌ User {user_id} disconnected.")
        active_connections.pop(user_id, None)
