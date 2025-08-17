# app/core/seeder.py
from __future__ import annotations

import logging
from typing import Iterable, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Organization, Role, User
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
    #    Make sure SUPERADMINS is an iterable of user ids (not a single string)
    raw_superadmins = settings.SUPERADMINS or set()
    if isinstance(raw_superadmins, str):
        superadmins: Set[str] = {s.strip() for s in raw_superadmins.split(",") if s.strip()}
    else:
        superadmins: Iterable[str] = raw_superadmins

    # We'll commit once at the end
    for clerk_user_id in superadmins:
        cid = clerk_user_id.strip()
        if not cid:
            continue

        # Fetch user with roles eagerly to avoid async lazy-load
        u = await db.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.clerk_user_id == cid)
        )

        if u:
            # ensure organization
            if u.organization_id != system_org.id:
                u.organization_id = system_org.id

            # ensure superadmin role (compare by id, not by instance)
            if not any(r.id == super_role.id for r in u.roles):
                u.roles.append(super_role)

            log.info("Updated superadmin user (clerk_id=%s)", cid)
        else:
            # Create minimal local user row
            u = User(
                clerk_user_id=cid,
                email=f"{cid}@example.com",
                full_name=f"User {cid}",
                organization_id=system_org.id,
                hashed_password="",
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            # Add + flush to get PK, then attach role
            db.add(u)
            await db.flush()
            u.roles = [super_role]

            log.info("Created superadmin user (clerk_id=%s)", cid)

    await db.commit()
    log.info("Seeding complete.")
