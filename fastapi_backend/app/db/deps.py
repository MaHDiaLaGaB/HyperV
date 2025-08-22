from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users.db import SQLAlchemyUserDatabase
from .database import async_session_maker
from app.models.users.users import User

# Primary dependency used across the app
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# Backwards-compat alias (your old name)
get_async_session = get_db
