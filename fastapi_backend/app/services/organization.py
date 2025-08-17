from __future__ import annotations
from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.models.users.users import User
from app.repositories import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from .base import BaseService
from app.security.clerk import CurrentUser


class OrganizationService(BaseService[OrganizationRepository]):
    """
    Service for managing Organization entities,
    with global superuser and tenant-scoped operations.
    """

    async def create_org(
        self,
        current_user: CurrentUser,
        data: OrganizationCreate,
    ) -> OrganizationRead:
        """
        Create a new organization. Only superusers may create.
        """
        if not current_user["is_superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to create organization",
            )

        if await self.repo.exists(slug=data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slug already in use",
            )

        org = self.repo.model(**data.model_dump(exclude_none=True))
        await self.repo.create(org)
        return OrganizationRead.model_validate(org)

    async def get_org(
        self,
        current_user: CurrentUser,
        org_id: UUID,
    ) -> OrganizationRead:
        """
        Fetch an organization by ID. Only superusers may fetch.
        """
        if not current_user["is_superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to view organization",
            )

        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return OrganizationRead.model_validate(org)

    async def update_org(
        self,
        current_user: CurrentUser,
        org_id: UUID,
        data: OrganizationUpdate,
    ) -> OrganizationRead:
        """
        Update an organization's details. Only superusers may update.
        """
        if not current_user["is_superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to update organization",
            )

        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        update_data = data.model_dump(exclude_none=True)
        if "slug" in update_data and await self.repo.exists(
            slug=update_data["slug"], id__ne=org_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slug already in use",
            )

        updated = await self.repo.update(org, update_data)
        return OrganizationRead.model_validate(updated)

    async def delete_org(
        self,
        current_user: CurrentUser,
        org_id: UUID,
    ) -> None:
        """
        Delete an organization. Only superusers may delete.
        """
        if not current_user["is_superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to delete organization",
            )

        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self.repo.delete(org)

    async def list_orgs(
        self,
        current_user: CurrentUser,
    ) -> List[OrganizationRead]:
        """
        List all organizations. Only superusers may list.
        """
        if not current_user["is_superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to list organizations",
            )

        orgs = await self.repo.list()
        return [OrganizationRead.model_validate(o) for o in orgs]
