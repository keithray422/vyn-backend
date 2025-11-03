# ---------- REGISTER & VERIFY PHONE FLOW ----------
import random
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.api.v1.schemas import UserCreate, UserResponse
from app.models.user import User
from app.core.security import create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    1️⃣ Register with username + phone number.
    2️⃣ Generate verification code.
    3️⃣ Return user info.
    """
    # Check duplicates
    result = await db.execute(select(User).where(User.phone_number == user_data.phone_number))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered.")

    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_username = result.scalars().first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken.")

    verification_code = str(random.randint(1000, 9999))

    new_user = User(
        phone_number=user_data.phone_number,
        username=user_data.username,
        is_verified=False,
        verification_code=verification_code
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logging.warning(f"📱 Mock SMS sent to {new_user.phone_number}: Your Vyn verification code is {verification_code}")

    return new_user

@router.post("/verify-phone")
async def verify_phone(data: dict, db: AsyncSession = Depends(get_db)):
    """
    ✅ Verify phone or resend code.
    If only phone_number is provided → resend code.
    If phone_number + code → verify.
    """
    phone = data.get("phone_number")
    code = data.get("code")

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required.")

    # Fetch user
    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # CASE 1: Resend code (only phone provided)
    if not code:
        new_code = str(random.randint(1000, 9999))
        user.verification_code = new_code
        await db.commit()
        logging.warning(f"📱 Resent SMS to {user.phone_number}: Your new Vyn verification code is {new_code}")
        return {"message": "Verification code resent."}

    # CASE 2: Verify code
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified.")

    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    user.is_verified = True
    user.verification_code = None
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "message": "Phone verified successfully!",
        "access_token": access_token,
        "token_type": "bearer"
    }
