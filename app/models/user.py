from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
