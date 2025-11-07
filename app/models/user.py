from sqlalchemy import Column, Integer, String, Boolean
from app.db.database import Base

class User(Base):
    __tablename__ = "users"  # this must match the error message!

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    verification_code = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
