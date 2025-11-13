from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User

router = APIRouter()


# -------------------- SEND MESSAGE --------------------
@router.post("/messages")
async def send_message(
    sender_id: int = Query(...),
    receiver_id: int = Query(...),
    content: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        if not content.strip():
            raise HTTPException(status_code=400, detail="Message content cannot be empty.")

        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content.strip(),
            timestamp=datetime.utcnow(),
            is_read=False,
        )

        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

        return {
            "data": {
                "id": new_message.id,
                "sender_id": new_message.sender_id,
                "receiver_id": new_message.receiver_id,
                "content": new_message.content,
                "timestamp": new_message.timestamp.isoformat(),
                "is_read": new_message.is_read,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- GET MESSAGES BETWEEN TWO USERS --------------------
@router.get("/messages/{user_id}/{other_user_id}")
async def get_messages_between_users(user_id: int, other_user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Message)
            .where(
                ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id))
                | ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
            )
            .order_by(Message.timestamp)
        )
        messages = result.scalars().all()

        # Convert message objects to dicts
        return [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "is_read": msg.is_read,
            }
            for msg in messages
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- MARK MESSAGES AS READ --------------------
@router.post("/messages/read")
async def mark_messages_as_read(
    user_id: int = Query(...),
    other_user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(Message).where(
                (Message.sender_id == other_user_id)
                & (Message.receiver_id == user_id)
                & (Message.is_read == False)
            )
        )
        unread_msgs = result.scalars().all()

        for msg in unread_msgs:
            msg.is_read = True

        await db.commit()
        return {"updated": len(unread_msgs)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
