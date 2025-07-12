from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar
from app.repositories.base import AsyncRepository

RepoT = TypeVar("RepoT", bound=AsyncRepository)

class BaseService(Generic[RepoT]):
    """Common helper for wrapping repository calls inside explicit transactions."""

    def __init__(self, repo: RepoT, db: AsyncSession):
        self.repo = repo
        self.db = db

    async def _commit(self):
        """Explicit commit helper; may be overridden to add audit."""
        await self.db.commit()