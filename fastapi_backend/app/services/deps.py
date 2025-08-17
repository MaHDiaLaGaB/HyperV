"""FastAPI dependency factories for injecting Service objects."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_async_session
from app.repositories.deps import (
    get_organization_repo,
    get_role_repo,
    get_permission_repo,
    get_user_repo,
    get_pipeline_repo,
    get_asset_repo,
    get_event_repo,
    get_alert_repo,
    get_report_repo,
)
from app.repositories import (
    OrganizationRepository,
    RoleRepository,
    PermissionRepository,
    UserRepository,
    PipelineRepository,
    AssetRepository,
    EventRepository,
    AlertRepository,
    ReportRepository,
)
from app.security.clerk import get_current_user
from app.services.organization import OrganizationService
from app.services.role import RoleService
from app.services.users import UserService
from app.services.pipeline import PipelineService
from app.services.asset import AssetService
from app.services.event import EventService
from app.services.alert import AlertService
from app.services.report import ReportService


async def get_organization_service(
    org_repo: OrganizationRepository = Depends(get_organization_repo),
    db: AsyncSession = Depends(get_async_session),
) -> OrganizationService:
    """Injectable OrganizationService"""
    return OrganizationService(org_repo, db)


async def get_role_service(
    role_repo: RoleRepository = Depends(get_role_repo),
    perm_repo: PermissionRepository = Depends(get_permission_repo),
    db: AsyncSession = Depends(get_async_session),
) -> RoleService:
    """Injectable RoleService"""
    return RoleService(role_repo, perm_repo, db)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo),
    user_manager=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> UserService:
    """Injectable UserService"""
    return UserService(user_repo, role_repo, user_manager, db)


async def get_pipeline_service(
    pipeline_repo: PipelineRepository = Depends(get_pipeline_repo),
    db: AsyncSession = Depends(get_async_session),
) -> PipelineService:
    """Injectable PipelineService"""
    return PipelineService(pipeline_repo, db)


async def get_asset_service(
    asset_repo: AssetRepository = Depends(get_asset_repo),
    db: AsyncSession = Depends(get_async_session),
) -> AssetService:
    """Injectable AssetService"""
    return AssetService(asset_repo, db)


async def get_event_service(
    event_repo: EventRepository = Depends(get_event_repo),
    alert_repo: AlertRepository = Depends(get_alert_repo),
    db: AsyncSession = Depends(get_async_session),
) -> EventService:
    """Injectable EventService"""
    return EventService(event_repo, alert_repo, db)


async def get_alert_service(
    alert_repo: AlertRepository = Depends(get_alert_repo),
    db: AsyncSession = Depends(get_async_session),
) -> AlertService:
    """Injectable AlertService"""
    return AlertService(alert_repo, db)


async def get_report_service(
    report_repo: ReportRepository = Depends(get_report_repo),
    db: AsyncSession = Depends(get_async_session),
) -> ReportService:
    """Injectable ReportService"""
    return ReportService(report_repo, db)


__all__ = [
    "get_organization_service",
    "get_role_service",
    "get_user_service",
    "get_pipeline_service",
    "get_asset_service",
    "get_event_service",
    "get_alert_service",
    "get_report_service",
]
