from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Role
from .base import AsyncRepository, AsyncSession
from .mixins import OrgFilterMixin


class RoleRepository(OrgFilterMixin, AsyncRepository[Role]):
    model = Role

    async def list_with_permissions(self, org_id: int) -> List[Role]:
        stmt = (
            select(Role)
            .where(Role.organization_id == org_id)
            .options(selectinload(Role.permissions))
        )
        res = await self.db.scalars(stmt)
        return list(res)
