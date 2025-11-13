from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc, text
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User
from datetime import datetime

router = APIRouter()

# -------------------- SEND MESSAGE --------------------
@router.post("/messages")
async def send_message(sender_id: int, receiver_id: int, content: str, db: AsyncSession = Depends(get_db)):
    """
    Send a message from one user to another.
    """
    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    new_message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow(),
        is_read=False
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {"message": "Message sent successfully.", "data": {
        "id": new_message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "timestamp": new_message.timestamp
    }}


# -------------------- FETCH CHAT BETWEEN TWO USERS --------------------
@router.get("/messages/{user_id}/{other_user_id}")
async def get_messages(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all messages between two users (both directions).
    """
    query = await db.execute(
        select(Message)
        .where(
            or_(
                (Message.sender_id == user_id) & (Message.receiver_id == other_user_id),
                (Message.sender_id == other_user_id) & (Message.receiver_id == user_id)
            )
        )
        .order_by(Message.timestamp.asc())
    )
    messages = query.scalars().all()

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found between these users.")

    return [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "is_read": msg.is_read
        }
        for msg in messages
    ]


# -------------------- FETCH CHAT LIST (RECENT CHATS) --------------------
@router.get("/chats/{user_id}")
async def get_chat_list(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns list of users the given user has chatted with,
    showing the latest message and timestamp for each conversation.
    """
    result = await db.execute(text(f"""
        SELECT DISTINCT ON (other_user_id)
            other_user_id, content, timestamp
        FROM (
            SELECT
                CASE
                    WHEN sender_id = {user_id} THEN receiver_id
                    ELSE sender_id
                END AS other_user_id,
                content,
                timestamp
            FROM messages
            WHERE sender_id = {user_id} OR receiver_id = {user_id}
            ORDER BY timestamp DESC
        ) subquery
        ORDER BY other_user_id, timestamp DESC
    """))

    rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No chats found.")

    chat_list = []
    for row in rows:
        other_id = row[0]
        user_query = await db.execute(select(User).where(User.id == other_id))
        other_user = user_query.scalars().first()
        chat_list.append({
            "user_id": other_id,
            "username": other_user.username if other_user else "Unknown",
            "last_message": row[1],
            "timestamp": row[2]
        })

    return chat_list
#--------------------END OF FILE--------------
