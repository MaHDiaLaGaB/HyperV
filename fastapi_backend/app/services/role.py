from __future__ import annotations
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role import RoleCreate, RoleRead, RolePermissionsUpdate
from app.repositories import RoleRepository, PermissionRepository
from .base import BaseService


class RoleService(BaseService[RoleRepository]):
    """
    Service for managing Role entities, scoped to an organization.
    """

    def __init__(
        self,
        repo: RoleRepository,
        perm_repo: PermissionRepository,
        db: AsyncSession,
    ):
        super().__init__(repo, db)
        self.perm_repo = perm_repo

    async def create_role(
        self,
        org_id: int,
        data: RoleCreate,
    ) -> RoleRead:
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
        return RoleRead.model_validate(role)

    async def get_role(
        self,
        org_id: int,
        role_id: int,
    ) -> RoleRead:
        role = await self.repo.get(role_id)
        if not role or role.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found in this organization",
            )
        return RoleRead.model_validate(role)

    async def list_roles(
        self,
        org_id: int,
    ) -> List[RoleRead]:
        roles = await self.repo.list_with_permissions(org_id)
        return [RoleRead.model_validate(r) for r in roles]

    async def assign_permissions(
        self,
        org_id: int,
        role_id: int,
        data: RolePermissionsUpdate,
    ) -> RoleRead:
        role = await self.repo.get(role_id)
        if not role or role.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found in this organization",
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
        return RoleRead.model_validate(role)
