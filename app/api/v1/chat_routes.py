# app/api/v1/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# -------------------- SCHEMAS --------------------
class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageUpdate(BaseModel):
    content: str


# -------------------- ROUTES --------------------

# ✅ Send message
@router.post("/messages")
async def send_message(data: MessageCreate, db: AsyncSession = Depends(get_db)):
    new_msg = Message(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        content=data.content,
        status="sent",
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    return {
        "id": new_msg.id,
        "sender_id": new_msg.sender_id,
        "receiver_id": new_msg.receiver_id,
        "content": new_msg.content,
        "timestamp": new_msg.timestamp,
        "status": new_msg.status,
    }


# ✅ Get messages between two users
@router.get("/messages/{user_id}/{other_user_id}")
async def get_messages(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Message).where(
            ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
        ).order_by(Message.timestamp)
    )
    messages = query.scalars().all()
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "timestamp": m.timestamp,
            "status": m.status,
        }
        for m in messages
    ]


# ✅ Mark all messages from `other_user_id` to `user_id` as read
@router.put("/messages/read/{user_id}/{other_user_id}")
async def mark_as_read(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Message).where(
            (Message.sender_id == other_user_id) & (Message.receiver_id == user_id)
        )
    )
    messages = query.scalars().all()

    if not messages:
        return {"message": "No messages to update"}

    for msg in messages:
        msg.status = "read"
    await db.commit()
    return {"message": "Messages marked as read"}


# ✅ Edit message
@router.put("/messages/{message_id}")
async def edit_message(message_id: int, data: MessageUpdate, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Message).where(Message.id == message_id))
    msg = query.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.content = data.content
    await db.commit()
    return {"message": "Message updated"}


# ✅ Delete message
@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Message).where(Message.id == message_id))
    msg = query.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    await db.delete(msg)
    await db.commit()
    return {"message": "Message deleted"}
