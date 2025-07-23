# app/core/seeder.py
from uuid import uuid4
import logging

from fastapi_users.manager import BaseUserManager
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_users.password import PasswordHelper
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# use the same hasher(s) your app is configured with
password_helper = PasswordHelper(PasswordHash((Argon2Hasher(),)))

from app.core.config import settings
from app.models import Organization, Role
from app.models.users.users import User
from app.repositories import (
    OrganizationRepository,
    RoleRepository,
    UserRepository,
)
from app.schemas.enums import ClientType
from app.schemas.users import UserCreate

logging.basicConfig(level=logging.INFO)


async def seed_superuser(db: AsyncSession) -> None:
    """
    Ensure a global superuser exists, using only repositories.
    """
    # 1) Create or fetch the 'system' org
    org_repo = OrganizationRepository(db)
    if await org_repo.exists(slug="__system__"):
        [system] = await org_repo.list(
            filters=[Organization.slug == "__system__"],
            limit=1,
        )
    else:
        system = await org_repo.create(
            Organization(
                name="System",
                slug="__system__",
                client_type=ClientType.SYSTEM,
            )
        )
    logging.info(f"Using organization: {system.name} ({system.slug} {system.id})")

    # 2) Create or fetch the 'superadmin' role
    role_repo = RoleRepository(db)
    if await role_repo.exists(organization_id=system.id, name="superadmin"):
        [super_role] = await role_repo.list(
            filters=[
                Role.organization_id == system.id,
                Role.name == "superadmin",
            ],
            limit=1,
        )
    else:
        super_role = await role_repo.create(
            Role(
                name="superadmin",
                organization_id=system.id,
            )
        )

    user_repo = UserRepository(db)
    if not await user_repo.exists(email=settings.SUPERUSER_EMAIL):
        # 1) hash the password exactly the same way FastAPI‑Users would
        hashed = password_helper.hash(settings.SUPERUSER_PASSWORD)

        # 2) construct the ORM object
        new_user = User(
            id=uuid4(),
            email=settings.SUPERUSER_EMAIL,
            hashed_password=hashed,
            full_name=settings.SUPERUSER_FULL_NAME,
            organization_id=system.id,
            is_superuser=True,
            is_active=True,      # usually you want default-active and default-verified
            is_verified=True,
        )

        # create but don't commit yet
        created = await user_repo.create(new_user, commit=False)

        # now assign roles in-memory (no lazy load)
        created.roles = [super_role]

        # finally, write everything to the DB
        await db.commit()
