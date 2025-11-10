from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User
from pydantic import BaseModel
import traceback

router = APIRouter()

# -------------------- SCHEMAS --------------------
class SendMessageRequest(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

# -------------------- ROUTES --------------------

@router.post("/messages/send")
async def send_message(data: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    try:
        # ✅ Ensure sender and receiver exist
        sender = await db.execute(select(User).where(User.id == data.sender_id))
        receiver = await db.execute(select(User).where(User.id == data.receiver_id))
        sender_user = sender.scalars().first()
        receiver_user = receiver.scalars().first()

        if not sender_user or not receiver_user:
            raise HTTPException(status_code=404, detail="Sender or receiver not found.")

        # ✅ Create message
        new_message = Message(
            sender_id=data.sender_id,
            receiver_id=data.receiver_id,
            content=data.content
        )
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

        return {"message": {
            "id": new_message.id,
            "sender_id": new_message.sender_id,
            "receiver_id": new_message.receiver_id,
            "content": new_message.content,
            "timestamp": new_message.timestamp.isoformat(),
        }}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Send error: {str(e)}")


@router.get("/messages/{user_id}")
async def get_user_messages(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch messages sent or received by a specific user.
    """
    try:
        result = await db.execute(
            select(Message).where((Message.sender_id == user_id) | (Message.receiver_id == user_id))
        )
        messages = result.scalars().all()

        # Convert to dicts
        formatted = [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ]
        return {"messages": formatted}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fetch error: {str(e)}")
