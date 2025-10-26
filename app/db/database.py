from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Retrieve the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create an async SQLAlchemy engine using asyncpg (PostgreSQL)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,        # Logs SQL statements for debugging; set False in production
    future=True       # Ensures SQLAlchemy 2.x style behavior
)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# Base class for all ORM models
Base = declarative_base()

# Dependency function to get a database session (for routes)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
