from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.permission import PermissionCreate, PermissionRead
from app.services.permissions import PermissionService
from app.repositories import PermissionRepository
from app.db.deps import get_db
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter()


def get_permission_service(
    session: AsyncSession = Depends(get_db),
) -> PermissionService:
    return PermissionService(PermissionRepository(session), session)


@router.post(
    "/",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new permission",
)
async def create_permission(
    data: PermissionCreate,
    current: CurrentUser = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    """Create a permission within the current user's organization."""
    return await service.create_permission(current, data)


@router.get(
    "/",
    response_model=List[PermissionRead],
    summary="List permissions for organization",
)
async def list_permissions(
    current: CurrentUser = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service),
) -> List[PermissionRead]:
    """List all permissions scoped to the current user's organization."""
    return await service.list_permissions(current)


@router.get(
    "/{permission_id}",
    response_model=PermissionRead,
    summary="Get a permission by ID",
    responses={404: {"description": "Permission not found in organization"}},
)
async def get_permission(
    permission_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    """Fetch a single permission, validating organization scope."""
    return await service.get_permission(current, permission_id)
