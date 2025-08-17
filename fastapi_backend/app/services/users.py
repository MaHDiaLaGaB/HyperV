# app/services/user.py

from __future__ import annotations
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import UserRepository, RoleRepository
from app.schemas.users import UserUpdate, UserRead
from .base import BaseService
from app.security.clerk import CurrentUser
from app.services.context import ctx_from_current_user


class UserService(BaseService[UserRepository]):
    """
    Service for managing User entities with Clerk-based identity.
    - Superadmin (global) can act across tenants.
    - Regular users are scoped to their active organization.
    """

    def __init__(
        self,
        repo: UserRepository,
        role_repo: RoleRepository,
        db: AsyncSession,
    ) -> None:
        super().__init__(repo, db)
        self.role_repo = role_repo

    # If you still need a way to create local user rows (no passwords),
    # implement a separate 'provision_user' method. Clerk owns registration.

    async def update_profile(
        self,
        current: CurrentUser,
        user_id: UUID,
        data: UserUpdate,
    ) -> UserRead:
        """
        Update profile:
        - Superadmin may update any user.
        - Others may only update themselves within their org.
        """
        ctx = ctx_from_current_user(current)

        # Guard: non-superadmin can only update themselves
        if not ctx.is_superadmin and str(ctx.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to update this profile",
            )

        # Fetch target user within scope
        if ctx.is_superadmin:
            user = await self.repo.get(user_id)
        else:
            user = await self.repo.get_in_org(ctx.organization_id, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        updates = data.model_dump(exclude_none=True)

        # Password changes are managed by Clerk, not here
        if "password" in updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use Clerk to change password",
            )

        # Apply other updates
        if updates:
            await self.repo.update(user, updates)

        ur = UserRead.model_validate(user)
        ur.role_ids = [r.id for r in user.roles]
        ur.permission_ids = sorted({p.id for r in user.roles for p in r.permissions})
        return ur

    async def assign_roles(
        self,
        current: CurrentUser,
        user_id: UUID,
        role_ids: List[UUID],
    ) -> UserRead:
        """
        Assign roles:
        - Superadmin may assign roles to any user.
        - Org-scoped users may only assign roles within their org.
        """
        ctx = ctx_from_current_user(current)

        # Fetch user within scope
        if ctx.is_superadmin:
            user = await self.repo.get(user_id)
        else:
            user = await self.repo.get_in_org(ctx.organization_id, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Build filters to fetch roles by ids (and org if not superadmin)
        filters = [self.role_repo.model.id.in_(role_ids)]
        if not ctx.is_superadmin:
            filters.insert(0, self.role_repo.model.organization_id == ctx.organization_id)

        roles = await self.role_repo.list(filters=filters)
        if len(roles) != len(role_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or out-of-scope role IDs",
            )

        user.roles = roles
        await self._commit()

        ur = UserRead.model_validate(user)
        ur.role_ids = [r.id for r in roles]
        ur.permission_ids = sorted({p.id for r in roles for p in r.permissions})
        return ur

    async def list_users(
        self,
        current: CurrentUser,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserRead]:
        """
        List users:
        - Superadmin sees all; org users see only their organization's.
        """
        ctx = ctx_from_current_user(current)

        if ctx.is_superadmin:
            users = await self.repo.list(limit=limit, offset=offset)  # type: ignore
        else:
            users = await self.repo.list_by_org(ctx.organization_id, limit=limit, offset=offset)

        result: list[UserRead] = []
        for u in users:
            ur = UserRead.model_validate(u)
            ur.role_ids = [r.id for r in u.roles]
            ur.permission_ids = sorted({p.id for r in u.roles for p in r.permissions})
            result.append(ur)
        return result

    async def get_user(
        self,
        current: CurrentUser,
        user_id: UUID,
    ) -> UserRead:
        """
        Get a user by ID:
        - Superadmin may fetch any; org users only theirs.
        """
        ctx = ctx_from_current_user(current)

        if ctx.is_superadmin:
            user = await self.repo.get_with_roles(user_id)
        else:
            user = await self.repo.get_with_roles(ctx.organization_id, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        ur = UserRead.model_validate(user)
        ur.role_ids = [r.id for r in user.roles]
        ur.permission_ids = sorted({p.id for r in user.roles for p in r.permissions})
        return ur
