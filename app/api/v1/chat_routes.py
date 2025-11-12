from fastapi import APIRouter, WebSocket, Depends, HTTPException
from app.db.database import get_db
from app.models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import json
from fastapi import Body

router = APIRouter()
active_connections = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"✅ User {user_id} connected")

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            # Typing indicator
            if msg_data.get("type") == "typing":
                target = msg_data["to"]
                if target in active_connections:
                    await active_connections[target].send_text(json.dumps(msg_data))
                continue

            # Save message to DB
            message = Message(
                sender_id=msg_data["sender_id"],
                receiver_id=msg_data["receiver_id"],
                content=msg_data["content"],
                timestamp=datetime.utcnow(),
                seen=False,
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)

            # Send to receiver if online
            receiver_id = msg_data["receiver_id"]
            if receiver_id in active_connections:
                await active_connections[receiver_id].send_text(json.dumps({
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "content": message.content,
                    "timestamp": str(message.timestamp),
                    "seen": True,
                }))
                # Mark as seen
                message.seen = True
                await db.commit()

            # Confirm to sender
            await websocket.send_text(json.dumps({
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "timestamp": str(message.timestamp),
                "seen": message.seen,
            }))

    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
    finally:
        del active_connections[user_id]
        await websocket.close()


# ✅ Fetch all messages between two users
@router.get("/messages/{user1_id}/{user2_id}")
async def get_chat_history(user1_id: int, user2_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Message)
            .where(
                ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id))
                | ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
            )
            .order_by(Message.timestamp)
        )
        messages = result.scalars().all()

        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "content": m.content,
                "timestamp": str(m.timestamp),
                "seen": m.seen,
            }
            for m in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Delete a specific message by ID
@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await db.delete(message)
    await db.commit()
    return {"message": "Message deleted successfully", "deleted_id": message_id}


# ✅ Edit message content by ID
@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int, 
    data: dict = Body(...), 
    db: AsyncSession = Depends(get_db)
):
    new_content = data.get("content")
    if not new_content:
        raise HTTPException(status_code=400, detail="Missing new content")

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.content = new_content
    await db.commit()
    await db.refresh(message)
    return {
        "message": "Message updated successfully",
        "updated": {
            "id": message.id,
            "content": message.content,
            "timestamp": str(message.timestamp),
        },
    }
