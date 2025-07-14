from __future__ import annotations
from typing import List, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Event
from .base import AsyncRepository
from .mixins import OrgFilterMixin


class EventRepository(OrgFilterMixin, AsyncRepository[Event]):
    model = Event

    async def list_with_related(self, org_id: UUID) -> List[Any]:
        stmt = (
            select(Event)
            .where(Event.organization_id == org_id)
            .options(selectinload(Event.asset), selectinload(Event.pipeline))
        )
        res = await self.db.scalars(stmt)
        return list(res)
