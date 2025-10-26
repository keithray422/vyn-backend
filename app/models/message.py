from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base
from app.models.user import User

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey(User.id))
    receiver_id = Column(Integer, ForeignKey(User.id))
    content = Column(String, nullable=False)
