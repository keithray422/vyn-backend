from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Message, User
from app.db.database import get_db
from app.api.v1.message_schemas import MessageSchema

router = APIRouter()

@router.post("/messages")
async def send_message(message: MessageSchema, db: Session = Depends(get_db)):
    """
    Create and send a new message.
    """
    try:
        new_message = models.Message(
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            content=message.content
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return {
            "status": "success",
            "message": {
                "id": new_message.id,
                "sender_id": new_message.sender_id,
                "receiver_id": new_message.receiver_id,
                "content": new_message.content,
                "timestamp": new_message.timestamp
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/messages/{user_id}")
async def get_user_messages(user_id: int, db: Session = Depends(get_db)):
    """
    Get all messages for a specific user.
    """
    try:
        messages = db.query(models.Message).filter(
            (models.Message.sender_id == user_id) |
            (models.Message.receiver_id == user_id)
        ).all()

        return {"status": "success", "messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")
