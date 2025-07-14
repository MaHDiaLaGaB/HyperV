from __future__ import annotations
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users import exceptions as fau_exc
from fastapi_users.manager import BaseUserManager

from app.schemas.users import UserCreate, UserUpdate, UserRead
from app.repositories import UserRepository, RoleRepository
from .base import BaseService


class UserService(BaseService[UserRepository]):
    """
    Service for managing User entities, scoped to an organization.
    """

    def __init__(
        self,
        repo: UserRepository,
        role_repo: RoleRepository,
        user_manager: BaseUserManager,
        db: AsyncSession,
    ):
        super().__init__(repo, db)
        self.role_repo = role_repo
        self.user_manager = user_manager

    async def register(self, data: UserCreate) -> UserRead:
        """
        Create a new user account.
        Raises 409 if email already exists.
        """
        try:
            user_db = await self.user_manager.create(data.model_dump())
        except fau_exc.UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return UserRead.model_validate(user_db)

    async def update_profile(
        self,
        org_id: int,
        user_id: UUID,
        data: UserUpdate,
    ) -> UserRead:
        """
        Update a user's profile (name, active status, password).
        Users may update themselves; superusers may update any.
        """
        user = await self.repo.get_in_org(org_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this organization",
            )
        updates = data.model_dump(exclude_none=True)
        # Handle password separately to ensure hashing
        if "password" in updates:
            await self.user_manager.update(user, updates)
            # Remove password so we don't set it again below
            updates.pop("password")
        # Update other fields via repo
        if updates:
            await self.repo.update(user, updates)
        return UserRead.model_validate(user)

    async def assign_roles(
        self,
        org_id: int,
        user_id: UUID,
        role_ids: List[int],
    ) -> UserRead:
        """
        Assign a set of roles to a user within the same organization.
        Only superusers may call this.
        """
        user = await self.repo.get_in_org(org_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this organization",
            )
        # Fetch org-scoped roles
        roles = await self.role_repo.list(
            filters=[
                self.role_repo.model.organization_id == org_id,
                self.role_repo.model.id.in_(role_ids),
            ]
        )
        if len(roles) != len(role_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more role IDs are invalid or out of scope",
            )
        user.roles = roles
        await self._commit()
        return UserRead.model_validate(user)

    async def list_users(
        self,
        org_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserRead]:
        """
        List users within the organization, with pagination.
        """
        users = await self.repo.list(
            filters=[self.repo.model.organization_id == org_id],
            limit=limit,
            offset=offset,
        )
        return [UserRead.model_validate(u) for u in users]

    async def get_user(
        self,
        org_id: UUID,
        user_id: UUID,
    ) -> UserRead:
        """
        Get a single user by ID, scoped to organization.
        """
        user = await self.repo.get_with_roles(org_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this organization",
            )
        # Extract permission_ids from roles
        user_read = UserRead.model_validate(user)
        user_read.permission_ids = sorted(
            {p.id for r in user.roles for p in r.permissions}
        )
        user_read.role_ids = [r.id for r in user.roles]
        return user_read
