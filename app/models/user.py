# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(32), unique=True, index=True, nullable=False)
    username = Column(String(64), unique=True, index=True, nullable=False)

    # verification + basic flags
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(16), nullable=True)

    # optional: backref for messages if you have Message model relationships
    # messages_sent = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    # messages_received = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone_number} username={self.username}>"
