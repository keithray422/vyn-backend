# create_tables.py
# Creates all tables using the async engine defined in app.db.database
# This file uses SQLAlchemy's async engine and runs the create_all
# inside an async context so it works correctly with asyncpg.

import asyncio
from app.db.database import engine, Base

async def create_all_tables():
    # Use an async context so SQLAlchemy uses the async engine properly
    async with engine.begin() as conn:
        # run_sync will run the sync create_all() method on the connection's
        # synchronous engine in a thread via greenlet handling
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
