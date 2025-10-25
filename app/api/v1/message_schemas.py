from pydantic import BaseModel
from datetime import datetime

class MessageSchema(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

    class Config:
        orm_mode = True  # ✅ Enables SQLAlchemy compatibility
        from_attributes = True  # for Pydantic v2+
