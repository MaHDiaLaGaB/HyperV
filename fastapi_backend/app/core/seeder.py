# app/core/seeder.py
from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Organization, Role
from app.models import User  # adjust if your User model path differs
from app.repositories import (
    OrganizationRepository,
    RoleRepository,
    UserRepository,
)
from app.schemas.enums import ClientType

log = logging.getLogger(__name__)


async def seed_core(db: AsyncSession) -> None:
    """
    Seed minimal data needed for a Clerk-based setup:
      1) Ensure a System org with slug "__system__"
      2) Ensure a "superadmin" role in the System org
      3) Optionally upsert local user rows for each Clerk user id in settings.SUPERADMINS
         and attach the 'superadmin' role (purely for your app's role system).
    """
    org_repo = OrganizationRepository(db)
    role_repo = RoleRepository(db)
    user_repo = UserRepository(db)

    # 1) System org
    system_org = None
    if await org_repo.exists(slug="__system__"):
        [system_org] = await org_repo.list(
            filters=[Organization.slug == "__system__"], limit=1
        )
    else:
        system_org = await org_repo.create(
            Organization(
                name="System",
                slug="__system__",
                client_type=ClientType.SYSTEM,
            )
        )
    log.info("Using organization: %s (%s %s)", system_org.name, system_org.slug, system_org.id)

    # 2) "superadmin" role within System org
    super_role = None
    if await role_repo.exists(organization_id=system_org.id, name="superadmin"):
        [super_role] = await role_repo.list(
            filters=[Role.organization_id == system_org.id, Role.name == "superadmin"],
            limit=1,
        )
    else:
        super_role = await role_repo.create(
            Role(name="superadmin", organization_id=system_org.id)
        )
    log.info("Ensured role: %s (org=%s)", super_role.name, system_org.slug)

    # 3) Optional: upsert local user rows for Clerk superadmins
    #    This is not strictly required (we auto-provision on first request),
    #    but it's handy if you want the role pre-attached.
    superadmins: Iterable[str] = settings.SUPERADMINS or set()
    for clerk_user_id in superadmins:
        # skip empties
        clerk_user_id = clerk_user_id.strip()
        if not clerk_user_id:
            continue

        # Upsert local user by clerk_user_id
        if await user_repo.exists(clerk_user_id=clerk_user_id):
            [u] = await user_repo.list(
                filters=[User.clerk_user_id == clerk_user_id], limit=1
            )
            # ensure organization & role
            u.organization_id = system_org.id
            if super_role not in u.roles:
                u.roles = list({*u.roles, super_role})
            await db.commit()
            log.info("Updated superadmin user (clerk_id=%s)", clerk_user_id)
        else:
            # Create a minimal local user row with required fields
            u = User(
                clerk_user_id=clerk_user_id,
                email=f"{clerk_user_id}@example.com",  # Default email based on clerk_user_id
                full_name=f"User {clerk_user_id}",  # Default name based on clerk_user_id
                organization_id=system_org.id,
                hashed_password="",  # Empty password for Clerk users
                is_active=True,
                is_superuser=True,  # Superadmin users
                is_verified=True,
            )
            created = await user_repo.create(u, commit=False)
            created.roles = [super_role]
            await db.commit()
            log.info("Created superadmin user (clerk_id=%s)", clerk_user_id)

    log.info("Seeding complete.")
