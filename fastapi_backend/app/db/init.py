# app/db/init.py
from sqlalchemy import text
from .database import engine
from .base import Base

async def ensure_extensions():
    # Needed for server_default gen_random_uuid()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

# Dev-only helper (avoid in prod; use Alembic instead)
async def create_db_and_tables():
    await ensure_extensions()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
