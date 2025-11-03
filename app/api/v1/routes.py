from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.api.v1.schemas import UserCreate, UserResponse
from app.api.v1.user_service import create_user, get_user_by_phone
from app.core.security import create_access_token
from app.api.v1.schemas import Token
from sqlalchemy.future import select
from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import FastAPI
app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback, sys
    print("🔥 Backend error:", str(exc), file=sys.stderr)
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")

@router.get("/hello")
async def hello():
    return {"message": "Hello from Vyn backend!"}

# -------- User registration --------
import random
import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.api.v1.schemas import UserCreate, UserResponse
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.phone_number == user_data.phone_number))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Generate mock verification code
    verification_code = str(random.randint(1000, 9999))

    # Create new user
    new_user = User(
        phone_number=user_data.phone_number,
        username=user_data.username,
        is_verified=False,
        verification_code=verification_code
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log mock SMS
    logging.warning(f"📱 Mock SMS to {new_user.phone_number}: Your Vyn verification code is {verification_code}")

    return new_user


# -------- User login --------
@router.post("/login", response_model=Token)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_phone(db, user_data.phone_number)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
class VerifyPhoneRequest(BaseModel):
    phone_number: str
    code: str

@router.post("/verify-phone")
async def verify_phone(data: VerifyPhoneRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code.")
    
    user.is_verified = True
    user.verification_code = None
    await db.commit()
    await db.refresh(user)

    return {"message": "Phone number verified successfully!"}
