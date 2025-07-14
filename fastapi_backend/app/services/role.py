from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.users import User
from app.repositories import RoleRepository, PermissionRepository
from app.schemas.role import RoleCreate, RoleRead, RolePermissionsUpdate
from .base import BaseService


class RoleService(BaseService[RoleRepository]):
    """
    Service for managing Role entities,
    supporting both a global superuser and tenant-scoped operations.
    """

    def __init__(
        self,
        repo: RoleRepository,
        perm_repo: PermissionRepository,
        db: AsyncSession,
    ) -> None:
        super().__init__(repo, db)
        self.perm_repo = perm_repo

    async def create_role(
        self,
        current_user: User,
        data: RoleCreate,
    ) -> RoleRead:
        """
        Create a new role with permissions.
        Superusers may create in any organization;
        others only in their own.
        """
        # Determine organization context
        org_id = (
            data.organization_id
            if current_user.is_superuser
            else current_user.organization_id
        )
        # Validate permissions
        perms = await self.perm_repo.list(
            filters=[self.perm_repo.model.id.in_(data.permission_ids)]
        )
        if len(perms) != len(data.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permission IDs are invalid",
            )
        role = self.repo.model(
            organization_id=org_id,
            name=data.name,
            permissions=perms,
        )
        await self.repo.create(role)
        validated: RoleRead = RoleRead.model_validate(role)
        return validated

    async def get_role(
        self,
        current_user: User,
        role_id: UUID,
    ) -> RoleRead:
        """
        Fetch a role by ID. Superusers may fetch any;
        org users only theirs.
        """
        if current_user.is_superuser:
            role = await self.repo.get(role_id)
        else:
            role = await self.repo.get_in_org(current_user.organization_id, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        validated: RoleRead = RoleRead.model_validate(role)
        return validated

    async def list_roles(
        self,
        current_user: User,
        org_id: Optional[int] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[RoleRead]:
        """
        List roles. Superusers may specify org_id to list for any tenant;
        org users list within their own org.
        """
        if current_user.is_superuser:
            if org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="`org_id` must be provided for superusers",
                )
            roles = await self.repo.list_with_permissions(org_id)
        else:
            roles = await self.repo.list_with_permissions(current_user.organization_id)
        return [RoleRead.model_validate(r) for r in roles]

    async def assign_permissions(
        self,
        current_user: User,
        role_id: UUID,
        data: RolePermissionsUpdate,
    ) -> RoleRead:
        """
        Replace a role's permissions. Superusers may modify any;
        org users only their own roles.
        """
        if current_user.is_superuser:
            role = await self.repo.get(role_id)
        else:
            role = await self.repo.get_in_org(current_user.organization_id, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        perms = await self.perm_repo.list(
            filters=[self.perm_repo.model.id.in_(data.permission_ids)]
        )
        if len(perms) != len(data.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permission IDs are invalid",
            )
        role.permissions = perms
        await self._commit()
        validated: RoleRead = RoleRead.model_validate(role)
        return validated
