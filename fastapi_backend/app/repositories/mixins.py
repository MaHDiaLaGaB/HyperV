from __future__ import annotations
from uuid import UUID
from typing import Any, Generic, List, Optional, TypeVar, Protocol, runtime_checkable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class OrgEntity(Protocol):
    """
    Protocol for ORM models that must have 'organization_id' and 'id' attributes.
    """

    organization_id: Any
    id: Any


ModelT = TypeVar("ModelT", bound=OrgEntity)


class OrgFilterMixin(Generic[ModelT]):
    """Adds organization_id filtering helpers for multi-tenant isolation."""

    model: type[ModelT]  # SQLAlchemy model class implementing OrgEntity
    db: AsyncSession

    async def list_by_org(
        self,
        org_id: UUID,
        filters: Optional[List[Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ModelT]:
        """
        List records belonging to the given organization, with optional filters
        and pagination.
        """
        stmt = select(self.model).where(self.model.organization_id == org_id)
        if filters:
            for cond in filters:
                stmt = stmt.where(cond)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        results = await self.db.scalars(stmt)
        return list(results)

    async def get_in_org(
        self,
        org_id: UUID,
        obj_id: UUID,
    ) -> Optional[ModelT]:
        """
        Fetch a single record by primary key, only if it belongs to given org.
        """
        stmt = select(self.model).where(
            self.model.organization_id == org_id,
            self.model.id == obj_id,
        )
        result = await self.db.scalar(stmt)
        return result
