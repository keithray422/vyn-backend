# -------------------- HELPERS --------------------
import re
import random
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User

router = APIRouter()
logger = logging.getLogger("vyn.api.routes")


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to digits-only, no leading +.
    Examples:
      "0746 659 878" -> "746659878"
      "+254746659878" -> "254746659878"
      "0746659878" -> "746659878"
    """
    if not phone:
        return phone
    phone = phone.strip()
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0"):
        digits = digits[1:]
    return digits


def generate_verification_code():
    return str(random.randint(100000, 999999))


# -------------------- SCHEMAS --------------------
class RegisterRequest(BaseModel):
    phone_number: str
    username: str

class VerifyRequest(BaseModel):
    phone_number: str
    code: str

class ResendRequest(BaseModel):
    phone_number: str


# -------------------- ROUTES --------------------
@router.post("/register")
async def register_user(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        norm_phone = normalize_phone(data.phone_number)
        query = await db.execute(select(User).where(User.phone_number == norm_phone))
        existing_user = query.scalars().first()

        code = generate_verification_code()

        if existing_user:
            existing_user.verification_code = code
            existing_user.is_verified = False
            await db.commit()
            return {"message": "Verification code resent.", "code": code, "user_id": existing_user.id}

        new_user = User(
            phone_number=norm_phone,
            username=data.username,
            verification_code=code,
            is_verified=False
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        print(f"📱 SMS sent to {norm_phone}: {code}")
        return {"message": "User registered successfully. Verification code sent.", "code": code, "user_id": new_user.id}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e)}
        )


@router.post("/verify")
async def verify_user(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    norm_phone = normalize_phone(data.phone_number)
    print(f"🔍 Verify payload (normalized): phone={norm_phone}, code={data.code}")

    query = await db.execute(select(User).where(User.phone_number == norm_phone))
    user = query.scalars().first()
    print(f"🔎 DB lookup result for {norm_phone}: {user}")

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    user.is_verified = True
    user.verification_code = None
    await db.commit()
    await db.refresh(user)

    print(f"✅ User {user.id} verified")
    return {"message": "User verified successfully.", "username": user.username, "user_id": user.id}


@router.post("/resend")
async def resend_code(data: ResendRequest, db: AsyncSession = Depends(get_db)):
    norm_phone = normalize_phone(data.phone_number)
    print(f"↩️ Resend request (normalized): phone={norm_phone}")

    query = await db.execute(select(User).where(User.phone_number == norm_phone))
    user = query.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    code = generate_verification_code()
    user.verification_code = code
    user.is_verified = False
    await db.commit()
    await db.refresh(user)

    print(f"📱 New SMS sent to {norm_phone}: {code} (user_id={user.id})")
    return {"message": "New verification code sent.", "code": code, "user_id": user.id}
