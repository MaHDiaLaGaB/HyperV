from __future__ import annotations
from typing import Any, Iterable, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class OrgFilterMixin:
    """Adds organisation_id filtering helpers for multi-tenant isolation."""

    async def list_by_org(self, org_id: int, *filters, limit: int | None = None, offset: int | None = None):  # type: ignore[override]
        conds: List[Any] = [self.model.organization_id == org_id]
        conds.extend(filters)
        return await super().list(filters=conds, limit=limit, offset=offset)  # type: ignore[misc]

    async def get_in_org(self, org_id: int, obj_id: int):  # type: ignore[override]
        stmt = select(self.model).where(self.model.organization_id == org_id, self.model.id == obj_id)
        res = await self.db.scalar(stmt)
        return res