from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users import exceptions as fau_exc
from fastapi_users.manager import BaseUserManager
from app.schemas import UserCreate, UserUpdate, UserRead
from app.repositories import UserRepository, RoleRepository
from .base import BaseService



class UserService(BaseService[UserRepository]):
    def __init__(self, repo: UserRepository, role_repo: RoleRepository, user_manager: BaseUserManager, db: AsyncSession):
        super().__init__(repo, db)
        self.role_repo = role_repo
        self.user_manager = user_manager

    async def register(self, data: UserCreate) -> UserRead:
        try:
            user_db = await self.user_manager.create(data.model_dump())
        except fau_exc.UserAlreadyExists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        return UserRead.model_validate(user_db)

    async def update_profile(self, org_id: int, user_id: UUID, data: UserUpdate) -> UserRead:
        user = await self.repo.get_in_org(org_id, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.repo.update(user, data.model_dump(exclude_none=True))
        return UserRead.model_validate(user)

    async def assign_roles(self, org_id: int, user_id: UUID, role_ids: List[int]):
        user = await self.repo.get_in_org(org_id, user_id)
        roles = await self.role_repo.list(filters=[self.role_repo.model.id.in_(role_ids)])
        user.roles = roles
        await self._commit()
