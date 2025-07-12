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
from app.security.auth import get_user_manager

from .organization import OrganizationService
from .role import RoleService
from .users import UserService
from .pipeline import PipelineService
from .asset import AssetService
from .event import EventService
from .alert import AlertService
from .report import ReportService

async def get_organization_service(
    org_repo=Depends(get_organization_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return OrganizationService(org_repo, db)

async def get_role_service(
    role_repo=Depends(get_role_repo),
    perm_repo=Depends(get_permission_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return RoleService(role_repo, perm_repo, db)

async def get_user_service(
    user_repo=Depends(get_user_repo),
    role_repo=Depends(get_role_repo),
    user_manager=Depends(get_user_manager),
    db: AsyncSession = Depends(get_async_session),
):
    return UserService(user_repo, role_repo, user_manager, db)

async def get_pipeline_service(
    pipeline_repo=Depends(get_pipeline_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return PipelineService(pipeline_repo, db)

async def get_asset_service(
    asset_repo=Depends(get_asset_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return AssetService(asset_repo, db)

async def get_event_service(
    event_repo=Depends(get_event_repo),
    alert_repo=Depends(get_alert_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return EventService(event_repo, alert_repo, db)

async def get_alert_service(
    alert_repo=Depends(get_alert_repo),
    db: AsyncSession = Depends(get_async_session),
):
    return AlertService(alert_repo, db)

async def get_report_service(
    report_repo=Depends(get_report_repo),
    db: AsyncSession = Depends(get_async_session),
):
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
