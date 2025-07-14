from __future__ import annotations
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionRead
from .base import BaseService


class PermissionService(BaseService[PermissionRepository]):
    """
    Service for managing Permission entities, scoped to an organization.
    """

    async def create_permission(
        self,
        org_id: int,
        data: PermissionCreate,
    ) -> PermissionRead:
        # Prevent duplicate codes within the organization
        exists = await self.repo.exists(
            organization_id=org_id,
            code=data.code,
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission code already exists in this organization",
            )
        perm = self.repo.model(
            organization_id=org_id,
            code=data.code,
            description=data.description,
        )
        await self.repo.create(perm)
        return PermissionRead.model_validate(perm)

    async def get_permission(
        self,
        org_id: int,
        permission_id: int,
    ) -> PermissionRead:
        perm = await self.repo.get(permission_id)
        if not perm or perm.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found in this organization",
            )
        return PermissionRead.model_validate(perm)

    async def list_permissions(
        self,
        org_id: int,
    ) -> List[PermissionRead]:
        perms = await self.repo.list(
            filters=[self.repo.model.organization_id == org_id]
        )
        return [PermissionRead.model_validate(p) for p in perms]
