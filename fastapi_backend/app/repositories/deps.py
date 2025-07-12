"""FastAPI *Depends* factories for each repository (explicit)."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_async_session
from app.repositories import (
    OrganizationRepository,
    PermissionRepository,
    RoleRepository,
    UserRepository,
    PipelineRepository,
    AssetRepository,
    EventRepository,
    AlertRepository,
    ReportRepository,
)

# Explicit factories (so IDEs can resolve them, tests can monkeypatch).

aSync = AsyncSession  # alias for brevity

async def get_organization_repo(session: aSync = Depends(get_async_session)) -> OrganizationRepository:  # noqa: N802
    return OrganizationRepository(session)

async def get_permission_repo(session: aSync = Depends(get_async_session)) -> PermissionRepository:
    return PermissionRepository(session)

async def get_role_repo(session: aSync = Depends(get_async_session)) -> RoleRepository:
    return RoleRepository(session)

async def get_user_repo(session: aSync = Depends(get_async_session)) -> UserRepository:
    return UserRepository(session)

async def get_pipeline_repo(session: aSync = Depends(get_async_session)) -> PipelineRepository:
    return PipelineRepository(session)

async def get_asset_repo(session: aSync = Depends(get_async_session)) -> AssetRepository:
    return AssetRepository(session)

async def get_event_repo(session: aSync = Depends(get_async_session)) -> EventRepository:
    return EventRepository(session)

async def get_alert_repo(session: aSync = Depends(get_async_session)) -> AlertRepository:
    return AlertRepository(session)

async def get_report_repo(session: aSync = Depends(get_async_session)) -> ReportRepository:
    return ReportRepository(session)


__all__ = [
    "get_organization_repo",
    "get_permission_repo",
    "get_role_repo",
    "get_user_repo",
    "get_pipeline_repo",
    "get_asset_repo",
    "get_event_repo",
    "get_alert_repo",
    "get_report_repo",
]
