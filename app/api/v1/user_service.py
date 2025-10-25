from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

async def create_user(db: AsyncSession, phone_number: str, username: str):
    # check if phone or username already exists
    result = await db.execute(select(User).where((User.phone_number == phone_number) | (User.username == username)))
    existing = result.scalars().first()
    if existing:
        return None  # user exists already

    new_user = User(phone_number=phone_number, username=username)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_phone(db: AsyncSession, phone_number: str):
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalars().first()
