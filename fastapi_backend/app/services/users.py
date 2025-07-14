### app/services/user.py
from __future__ import annotations
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users import exceptions as fau_exc
from fastapi_users.manager import BaseUserManager

from app.models.users.users import User
from app.repositories import UserRepository, RoleRepository
from app.schemas.users import UserCreate, UserUpdate, UserRead
from .base import BaseService


class UserService(BaseService[UserRepository]):
    """
    Service for managing User entities,
    supporting both global superuser access and organization-scoped operations.
    """

    def __init__(
        self,
        repo: UserRepository,
        role_repo: RoleRepository,
        user_manager: BaseUserManager,
        db: AsyncSession,
    ) -> None:
        super().__init__(repo, db)
        self.role_repo = role_repo
        self.user_manager = user_manager

    async def register(
        self,
        data: UserCreate,
    ) -> UserRead:
        """
        Create a new user account. Raises 409 if email exists.
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
        current_user: User,
        user_id: UUID,
        data: UserUpdate,
    ) -> UserRead:
        """
        Update profile:
        - Superusers may update any user.
        - Others may only update themselves within their org.
        """
        # Fetch target user
        if current_user.is_superuser:
            user = await self.repo.get(user_id)
        else:
            user = await self.repo.get_in_org(current_user.organization_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        updates = data.model_dump(exclude_none=True)
        # Handle password change
        if "password" in updates:
            await self.user_manager.update(user, updates)
            updates.pop("password")
        # Apply other updates
        if updates:
            await self.repo.update(user, updates)

        validated = UserRead.model_validate(user)
        # Attach roles and permissions
        validated.role_ids = [r.id for r in user.roles]
        validated.permission_ids = sorted(
            {p.id for r in user.roles for p in r.permissions}
        )
        return validated

    async def assign_roles(
        self,
        current_user: User,
        user_id: UUID,
        role_ids: List[UUID],
    ) -> UserRead:
        """
        Assign roles:
        - Superusers may assign any user.
        - Org users only assign within their org.
        """
        # Fetch user
        if current_user.is_superuser:
            user = await self.repo.get(user_id)
        else:
            user = await self.repo.get_in_org(current_user.organization_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        # Fetch roles within scope
        filters = [self.role_repo.model.id.in_(role_ids)]
        if not current_user.is_superuser:
            filters.insert(
                0, self.role_repo.model.organization_id == current_user.organization_id
            )
        roles = await self.role_repo.list(filters=filters)
        if len(roles) != len(role_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or out-of-scope role IDs",
            )
        user.roles = roles
        await self._commit()

        validated = UserRead.model_validate(user)
        validated.role_ids = [r.id for r in roles]
        validated.permission_ids = sorted({p.id for r in roles for p in r.permissions})
        return validated

    async def list_users(
        self,
        current_user: User,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserRead]:
        """
        List users:
        - Superusers see all; org users see only their organization's.
        """
        if current_user.is_superuser:
            users = await self.repo.list(limit=limit, offset=offset)  # type: ignore
        else:
            users = await self.repo.list_by_org(
                current_user.organization_id, limit=limit, offset=offset
            )
        result: list[UserRead] = []
        for u in users:
            ur = UserRead.model_validate(u)
            ur.role_ids = [r.id for r in u.roles]
            ur.permission_ids = sorted({p.id for r in u.roles for p in r.permissions})
            result.append(ur)
        return result

    async def get_user(
        self,
        current_user: User,
        user_id: UUID,
    ) -> UserRead:
        """
        Get a user by ID:
        - Superusers may fetch any; org users only theirs.
        """
        if current_user.is_superuser:
            user = await self.repo.get_with_roles(user_id)
        else:
            user = await self.repo.get_with_roles(current_user.organization_id, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        ur = UserRead.model_validate(user)
        ur.role_ids = [r.id for r in user.roles]
        ur.permission_ids = sorted({p.id for r in user.roles for p in r.permissions})
        return ur
