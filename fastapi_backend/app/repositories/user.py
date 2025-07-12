from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import User
from .base import AsyncRepository
from .mixins import OrgFilterMixin

class UserRepository(OrgFilterMixin, AsyncRepository[User]):
    model = User

    async def get_with_roles(self, org_id: int, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id, User.organization_id == org_id)
            .options(selectinload(User.roles))
        )
        return await self.db.scalar(stmt)
