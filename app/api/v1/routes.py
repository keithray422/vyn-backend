from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User
import random

router = APIRouter()

# -------------------- SCHEMAS --------------------
class RegisterRequest(BaseModel):
    phone_number: str
    username: str

class VerifyRequest(BaseModel):
    phone_number: str
    code: str

class ResendRequest(BaseModel):
    phone_number: str

# -------------------- HELPERS --------------------
async def generate_verification_code():
    return str(random.randint(100000, 999999))  # 6-digit code


# -------------------- ROUTES --------------------

# ✅ 1. REGISTER USER (create or resend code if exists)
@router.post("/register")
async def register_user(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.phone_number == data.phone_number))
    existing_user = query.scalars().first()

    code = await generate_verification_code()

    if existing_user:
        # Update existing user’s verification code
        existing_user.verification_code = code
        existing_user.is_verified = False
        await db.commit()
        return {"message": "Verification code resent.", "code": code}

    # Create a new user
    new_user = User(
        phone_number=data.phone_number,
        username=data.username,
        verification_code=code,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()

    # In production, integrate Twilio or Africa's Talking here
    print(f"📱 SMS sent to {data.phone_number}: {code}")

    return {"message": "User registered successfully. Verification code sent.", "code": code}


# ✅ 2. VERIFY USER (match SMS code)
@router.post("/verify")
async def verify_user(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    user.is_verified = True
    user.verification_code = None  # clear after success
    await db.commit()

    return {"message": "User verified successfully.", "username": user.username}


# ✅ 3. RESEND CODE
@router.post("/resend")
async def resend_code(data: ResendRequest, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    code = await generate_verification_code()
    user.verification_code = code
    user.is_verified = False
    await db.commit()

    print(f"📱 New SMS sent to {data.phone_number}: {code}")
    return {"message": "New verification code sent.", "code": code}
