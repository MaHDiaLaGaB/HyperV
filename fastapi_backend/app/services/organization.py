from __future__ import annotations
from typing import List
from fastapi import HTTPException, status

from app.repositories import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from .base import BaseService


class OrganizationService(BaseService[OrganizationRepository]):
    """
    Service for managing organizations (tenants).
    """

    async def create_org(
        self,
        data: OrganizationCreate,
    ) -> OrganizationRead:
        # ensure unique slug
        if await self.repo.exists(slug=data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Slug already in use"
            )
        org = self.repo.model(**data.model_dump(exclude_none=True))
        await self.repo.create(org)
        return OrganizationRead.model_validate(org)

    async def get_org(
        self,
        org_id: int,
    ) -> OrganizationRead:
        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        return OrganizationRead.model_validate(org)

    async def update_org(
        self,
        org_id: int,
        data: OrganizationUpdate,
    ) -> OrganizationRead:
        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        update_data = data.model_dump(exclude_none=True)
        # if slug is being updated, check uniqueness
        if "slug" in update_data and await self.repo.exists(
            slug=update_data["slug"], id__ne=org_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Slug already in use"
            )
        updated = await self.repo.update(org, update_data)
        return OrganizationRead.model_validate(updated)

    async def delete_org(
        self,
        org_id: int,
    ) -> None:
        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        await self.repo.delete(org)

    async def list_orgs(self) -> List[OrganizationRead]:
        orgs = await self.repo.list()
        return [OrganizationRead.model_validate(o) for o in orgs]
