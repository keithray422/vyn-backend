# app/api/v1/chat_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.database import get_db
from app.models.message import Message
from sqlalchemy import or_, and_, func
from app.models.user import User

router = APIRouter()

# 🟢 Get all messages between two users
@router.get("/messages/{user_id}/{other_user_id}")
async def get_messages(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = await db.execute(
            select(Message)
            .where(
                ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id))
                | ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
            )
            .order_by(Message.timestamp.asc())
        )
        messages = query.scalars().all()
        if not messages:
            return []  # ✅ Return empty list instead of Not Found

        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "content": m.content,
                "timestamp": m.timestamp,
                "is_read": m.is_read,
            }
            for m in messages
        ]
    except Exception as e:
        print("❌ Error loading messages:", e)
        raise HTTPException(status_code=500, detail=str(e))


# 🟢 Send a message
@router.post("/messages")
async def send_message(
    sender_id: int = Query(...),
    receiver_id: int = Query(...),
    content: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=datetime.utcnow(),
            is_read=False,
        )
        db.add(new_msg)
        await db.commit()
        await db.refresh(new_msg)

        return {
            "data": {
                "id": new_msg.id,
                "sender_id": new_msg.sender_id,
                "receiver_id": new_msg.receiver_id,
                "content": new_msg.content,
                "timestamp": new_msg.timestamp,
                "is_read": new_msg.is_read,
            }
        }
    except Exception as e:
        print("❌ Send message error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# 🟢 Mark a message as read
@router.post("/messages/{message_id}/read")
async def mark_as_read(message_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = await db.execute(select(Message).where(Message.id == message_id))
        msg = query.scalars().first()

        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")

        msg.is_read = True
        await db.commit()
        await db.refresh(msg)
        return {"message": "Marked as read"}
    except Exception as e:
        print("❌ Mark read error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# 🟢 Return list of conversation summaries for a user
@router.get("/conversations/{user_id}")
async def get_conversations(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Fetch all messages involving this user
        q = await db.execute(
            select(Message)
            .where((Message.sender_id == user_id) | (Message.receiver_id == user_id))
            .order_by(Message.timestamp.desc())
        )
        msgs = q.scalars().all()

        if not msgs:
            return []  # no chats yet

        conversations = {}

        for m in msgs:
            partner_id = m.receiver_id if m.sender_id == user_id else m.sender_id

            if partner_id not in conversations:
                # fetch user object
                q_user = await db.execute(select(User).where(User.id == partner_id))
                user = q_user.scalars().first()

                conversations[partner_id] = {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                    },
                    "last_message": m.content,
                    "timestamp": m.timestamp,
                    "unread_count": 0,
                }

        # Calculate unread counts
        for partner_id in conversations.keys():
            q2 = await db.execute(
                select(func.count()).select_from(Message).where(
                    (Message.sender_id == partner_id)
                    & (Message.receiver_id == user_id)
                    & (Message.is_read == False)
                )
            )
            conversations[partner_id]["unread_count"] = q2.scalar_one()

        # sort by latest message
        return sorted(conversations.values(), key=lambda x: x["timestamp"], reverse=True)

    except Exception as e:
        print("❌ get_conversations error:", e)
        raise HTTPException(status_code=500, detail=str(e))
