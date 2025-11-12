from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# ------------------- SCHEMAS -------------------
class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

# ------------------- ROUTES -------------------

# ✅ 1. Send a message
@router.post("/messages")
async def send_message(data: MessageCreate, db: AsyncSession = Depends(get_db)):
    sender = await db.get(User, data.sender_id)
    receiver = await db.get(User, data.receiver_id)

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver not found.")

    new_msg = Message(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        content=data.content,
        timestamp=datetime.utcnow(),
    )

    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)

    return {
        "message": "Message sent successfully",
        "data": {
            "id": new_msg.id,
            "sender_id": new_msg.sender_id,
            "receiver_id": new_msg.receiver_id,
            "content": new_msg.content,
            "timestamp": new_msg.timestamp,
        },
    }


# ✅ 2. Fetch chat history between two users
@router.get("/messages/{sender_id}/{receiver_id}")
async def get_chat_history(sender_id: int, receiver_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Message)
        .where(
            ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id))
            | ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
        )
        .order_by(Message.timestamp.asc())
    )
    messages = query.scalars().all()

    return [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages
    ]
