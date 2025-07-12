from __future__ import annotations
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import RoleCreate, RoleRead
from app.repositories import RoleRepository, PermissionRepository
from .base import BaseService

class RoleService(BaseService[RoleRepository]):
    def __init__(self, repo: RoleRepository, perm_repo: PermissionRepository, db: AsyncSession):
        super().__init__(repo, db)
        self.perm_repo = perm_repo

    async def create_role(self, org_id: int, data: RoleCreate) -> RoleRead:
        # validate permissions belong to same org or global
        perms = await self.perm_repo.list(filters=[self.perm_repo.model.id.in_(data.permission_ids)])
        if len(perms) != len(data.permission_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid permission IDs")
        role_db = self.repo.model(
            organization_id=org_id,
            name=data.name,
            permissions=perms,
        )
        await self.repo.create(role_db)
        return RoleRead.model_validate(role_db)

    async def assign_permissions(self, role_id: int, perm_ids: List[int]):
        role = await self.repo.get(role_id)
        perms = await self.perm_repo.list(filters=[self.perm_repo.model.id.in_(perm_ids)])
        role.permissions = perms
        await self._commit()