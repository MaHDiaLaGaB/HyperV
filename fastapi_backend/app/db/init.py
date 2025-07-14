# app/db/init.py
from .database import engine
from .base import Base


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
