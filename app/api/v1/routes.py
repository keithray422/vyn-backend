# app/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User
import random
import logging
import traceback

router = APIRouter()
logger = logging.getLogger("vyn.api.routes")


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
def generate_verification_code():
    # sync is fine here
    return str(random.randint(100000, 999999))  # 6-digit code


# -------------------- ROUTE HELPERS --------------------
def _server_error_resp(exc: Exception):
    # Return a simple JSON response while logging full traceback to server logs
    tb = traceback.format_exc()
    logger.error("Unhandled exception in route: %s\n%s", exc, tb)
    # Return sanitized message to client
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


# -------------------- ROUTES --------------------

@router.post("/register")
async def register_user(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.phone_number == data.phone_number))
        existing_user = result.scalars().first()

        code = generate_verification_code()

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
        await db.refresh(new_user)

        # In production: send SMS using provider. For now log.
        logger.info("📱 Mock SMS sent to %s : %s", data.phone_number, code)

        return {"message": "User registered successfully. Verification code sent.", "code": code, "user_id": new_user.id}
    except Exception as e:
        return _server_error_resp(e)


@router.post("/verify")
async def verify_user(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.phone_number == data.phone_number))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if user.verification_code != data.code:
            raise HTTPException(status_code=400, detail="Invalid verification code.")

        user.is_verified = True
        user.verification_code = None  # clear after success
        await db.commit()
        await db.refresh(user)

        return {"message": "User verified successfully.", "username": user.username}
    except HTTPException as he:
        raise he
    except Exception as e:
        return _server_error_resp(e)


@router.post("/resend")
async def resend_code(data: ResendRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.phone_number == data.phone_number))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        code = generate_verification_code()
        user.verification_code = code
        user.is_verified = False
        await db.commit()
        await db.refresh(user)

        logger.info("📱 New SMS sent to %s : %s", data.phone_number, code)
        return {"message": "New verification code sent.", "code": code}
    except HTTPException as he:
        raise he
    except Exception as e:
        return _server_error_resp(e)
