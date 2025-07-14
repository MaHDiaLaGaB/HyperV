### app/services/permission.py
from __future__ import annotations
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.users import User
from app.repositories import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionRead
from .base import BaseService


class PermissionService(BaseService[PermissionRepository]):
    """
    Service for managing Permission entities,
    supporting both global superuser access and organization-scoped operations.
    """

    async def create_permission(
        self,
        current_user: User,
        data: PermissionCreate,
    ) -> PermissionRead:
        """
        Create a new permission. Superusers may create for any org; others only for their org.
        """
        # Determine organization context
        org_id = (
            data.organization_id
            if current_user.is_superuser
            and getattr(data, "organization_id", None) is not None
            else current_user.organization_id
        )
        # Prevent duplicate codes
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
        validated: PermissionRead = PermissionRead.model_validate(perm)
        return validated

    async def get_permission(
        self,
        current_user: User,
        permission_id: UUID,
    ) -> PermissionRead:
        """
        Retrieve a permission by ID. Superusers may retrieve any; org users only theirs.
        """
        if current_user.is_superuser:
            perm = await self.repo.get(permission_id)
        else:
            perm = await self.repo.get_in_org(
                current_user.organization_id, permission_id
            )
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )
        validated: PermissionRead = PermissionRead.model_validate(perm)
        return validated

    async def list_permissions(
        self,
        current_user: User,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[PermissionRead]:
        """
        List permissions. Superusers see all; org users only theirs.
        """
        if current_user.is_superuser:
            perms = await self.repo.list(limit=limit, offset=offset)  # type: ignore
        else:
            perms = await self.repo.list_by_org(
                current_user.organization_id,
                limit=limit,
                offset=offset,
            )
        return [PermissionRead.model_validate(p) for p in perms]
