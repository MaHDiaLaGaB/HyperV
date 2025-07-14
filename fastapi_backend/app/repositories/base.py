from __future__ import annotations
from typing import Any, Generic, Iterable, List, Optional, TypeVar, Dict, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ClauseElement, func

from app.db.base import Base  # noqa: I001

ModelT = TypeVar("ModelT", bound=Base)


class AsyncRepository(Generic[ModelT]):
    """Generic async CRUD helper. Subclasses set `model` attribute."""

    model: Type[ModelT]
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, obj_id: Any) -> Optional[ModelT]:
        """Fetch a single record by primary key."""
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.db.scalar(stmt)
        return result

    async def list(
        self,
        *,
        filters: Optional[Iterable[ClauseElement]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ModelT]:
        """List records matching optional filters, with pagination."""
        stmt = select(self.model)
        if filters:
            for condition in filters:
                stmt = stmt.where(condition)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        results = await self.db.scalars(stmt)
        return list(results)

    async def create(
        self,
        obj_in: ModelT,
        *,
        commit: bool = True,
    ) -> ModelT:
        """Add a new record to the database."""
        self.db.add(obj_in)
        if commit:
            await self.db.commit()
            await self.db.refresh(obj_in)
        return obj_in

    async def update(
        self,
        obj_db: ModelT,
        obj_in: Dict[str, Any],
        *,
        commit: bool = True,
    ) -> ModelT:
        """Update fields on an existing record."""
        for key, value in obj_in.items():
            setattr(obj_db, key, value)
        if commit:
            await self.db.commit()
            await self.db.refresh(obj_db)
        return obj_db

    async def delete(
        self,
        obj_db: ModelT,
        *,
        commit: bool = True,
    ) -> None:
        """Delete a record from the database."""
        await self.db.delete(obj_db)
        if commit:
            await self.db.commit()

    async def exists(self, **kwargs: Any) -> bool:
        """Return True if a record matching kwargs exists."""
        stmt = select(func.count()).select_from(self.model).filter_by(**kwargs)
        count = await self.db.scalar(stmt)
        return bool(count)
