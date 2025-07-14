# app/core/seeder.py
from uuid import uuid4

from fastapi_users.manager import BaseUserManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users.users import User
from app.repositories import UserRepository, OrganizationRepository, RoleRepository, PermissionRepository
from app.schemas.organization import OrganizationCreate
from app.schemas.role import RoleCreate
from app.schemas.users import UserCreate
from app.services.organization import OrganizationService
from app.services.role import RoleService

async def seed_superuser(db: AsyncSession, user_manager: BaseUserManager) -> None:
    """
    Ensure a global superuser exists. Idempotent.
    """
    org_repo = OrganizationRepository(db)
    # 1) Create or fetch the 'system' org
    system = await org_repo.get_by(filters=[org_repo.model.slug == "__system__"])  # type: ignore
    if not system:
        org_svc = OrganizationService(org_repo, db)
        system = await org_svc.create_org(OrganizationCreate(
            name="System",
            slug="__system__"
        ))

    # 2) Ensure superadmin role
    role_repo = RoleRepository(db)
    super_role = await role_repo.get_by(filters=[
        role_repo.model.organization_id == system.id,  # type: ignore
        role_repo.model.name == "superadmin"           # type: ignore
    ])
    if not super_role:
        perm_repo = PermissionRepository(db)
        role_svc = RoleService(role_repo, perm_repo, db)
        # pass a dummy superuser so create_role uses override
        dummy = User(id=uuid4(), email=settings.SUPERUSER_EMAIL, is_superuser=True, organization_id=system.id)  # type: ignore
        super_role = await role_svc.create_role(dummy, RoleCreate(
            name="superadmin",
            permission_ids=[]
        ))

    # 3) Create superuser if missing
    user_repo = UserRepository(db)
    exists = await user_repo.exists(email=settings.SUPERUSER_EMAIL)
    if not exists:
        user_db = await user_manager.create(UserCreate(
            email=settings.SUPERUSER_EMAIL,
            password=settings.SUPERUSER_PASSWORD,
            full_name=settings.SUPERUSER_FULL_NAME,
            organization_id=system.id,
            is_superuser=True,
        ).model_dump())
        # Attach role
        user = await user_repo.get(user_db.id)
        user.roles = [super_role]
        await db.commit()
