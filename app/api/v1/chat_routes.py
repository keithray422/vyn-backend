# app/api/v1/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User
from app.models.message import Message
from sqlalchemy import or_
from datetime import datetime

router = APIRouter()


# -------------------- SCHEMAS --------------------
class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str


# -------------------- SEND MESSAGE --------------------
@router.post("/send_message")
async def send_message(data: MessageCreate, db: AsyncSession = Depends(get_db)):
    sender = await db.get(User, data.sender_id)
    receiver = await db.get(User, data.receiver_id)

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    new_message = Message(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        content=data.content,
        timestamp=datetime.utcnow()
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {"message": "Message sent", "data": {
        "id": new_message.id,
        "content": new_message.content,
        "timestamp": new_message.timestamp.isoformat()
    }}


# -------------------- GET MESSAGES BETWEEN TWO USERS --------------------
@router.get("/get_messages/{user_id}/{other_user_id}")
async def get_messages(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Message)
        .where(
            or_(
                (Message.sender_id == user_id) & (Message.receiver_id == other_user_id),
                (Message.sender_id == other_user_id) & (Message.receiver_id == user_id)
            )
        )
        .order_by(Message.timestamp)
    )

    messages = query.scalars().all()
    return {"messages": [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        }
        for m in messages
    ]}


# -------------------- GET CHATS (chat list) --------------------
@router.get("/get_chats/{user_id}")
async def get_chats(user_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Message)
        .where(or_(Message.sender_id == user_id, Message.receiver_id == user_id))
        .order_by(Message.timestamp.desc())
    )
    messages = query.scalars().all()

    chat_partners = {}
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
        if other_id not in chat_partners:
            other_user = await db.get(User, other_id)
            if other_user:
                chat_partners[other_id] = {
                    "id": other_id,
                    "username": other_user.username,
                    "last_message": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }

    return {"chats": list(chat_partners.values())}


# -------------------- SEARCH USERS --------------------
@router.get("/search_user")
async def search_user(query: str, db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(
        select(User).where(User.username.ilike(f"%{query}%"))
    )
    results = stmt.scalars().all()
    return {"results": [
        {"id": user.id, "username": user.username, "phone_number": user.phone_number}
        for user in results
    ]}
