from __future__ import annotations
from typing import List
from fastapi import HTTPException, status
from app.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
)
from app.repositories import OrganizationRepository
from .base import BaseService

class OrganizationService(BaseService[OrganizationRepository]):
    async def create_org(self, data: OrganizationCreate) -> OrganizationRead:
        # ensure unique slug
        if await self.repo.exists(slug=data.slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")
        org_db = await self.repo.create(self.repo.model(**data.model_dump()))
        return OrganizationRead.model_validate(org_db)

    async def update_org(self, org_id: int, data: OrganizationUpdate) -> OrganizationRead:
        org_db = await self.repo.get(org_id)
        if not org_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        updated = await self.repo.update(org_db, data.model_dump(exclude_none=True))
        return OrganizationRead.model_validate(updated)

    async def list_orgs(self) -> List[OrganizationRead]:
        return [OrganizationRead.model_validate(o) for o in await self.repo.list()]
