from __future__ import annotations
from typing import Any, Generic, Iterable, List, Optional, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Executable, func

from app.db.base import Base  # noqa: I001

ModelT = TypeVar("ModelT", bound=Base)


class AsyncRepository(Generic[ModelT]):
    """Generic async CRUD helper.

    Subclasses set `model` attribute.
    """

    model: type[ModelT]

    def __init__(self, db: AsyncSession):
        self.db = db

    # ────────────────────── Basic CRUD ────────────────────────────────────────
    async def get(self, obj_id: Any) -> Optional[ModelT]:
        stmt = select(self.model).where(self.model.id == obj_id)
        res = await self.db.scalar(stmt)
        return res

    async def list(self, *, filters: Optional[Iterable[Executable]] = None, limit: int | None = None, offset: int | None = None) -> List[ModelT]:
        stmt = select(self.model)
        for cond in filters or []:
            stmt = stmt.where(cond)
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        res = await self.db.scalars(stmt)
        return list(res)

    async def create(self, obj_in: ModelT, *, commit: bool = True) -> ModelT:
        self.db.add(obj_in)
        if commit:
            await self.db.commit()
            await self.db.refresh(obj_in)
        return obj_in

    async def update(self, obj_db: ModelT, obj_in: dict[str, Any], *, commit: bool = True) -> ModelT:
        for key, value in obj_in.items():
            setattr(obj_db, key, value)
        if commit:
            await self.db.commit()
            await self.db.refresh(obj_db)
        return obj_db

    async def delete(self, obj_db: ModelT, *, commit: bool = True) -> None:
        await self.db.delete(obj_db)
        if commit:
            await self.db.commit()

    # ────────────────────── Utilities ─────────────────────────────────────────
    async def exists(self, **kwargs) -> bool:
        stmt = select(func.count()).select_from(self.model).filter_by(**kwargs)
        res = await self.db.scalar(stmt)
        return bool(res)