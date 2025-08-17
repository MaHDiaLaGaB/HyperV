from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.services.organization import OrganizationService
from app.services.deps import get_organization_service
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter()


def require_superadmin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current["is_superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current


@router.post(
    "/create",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    data: OrganizationCreate,
    current: CurrentUser = Depends(require_superadmin),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationRead:
    """Create a new tenant organization (superadmin only)."""
    return await service.create_org(current_user=current, data=data)


@router.get(
    "/get",
    response_model=List[OrganizationRead],
    summary="List all organizations",
)
async def list_organizations(
    current: CurrentUser = Depends(require_superadmin),
    service: OrganizationService = Depends(get_organization_service),
) -> List[OrganizationRead]:
    """Retrieve all tenant organizations (superadmin only)."""
    return await service.list_orgs(current_user=current)


@router.get(
    "/{org_id}",
    response_model=OrganizationRead,
    summary="Get organization by ID",
    responses={404: {"description": "Organization not found"}},
)
async def get_organization(
    org_id: UUID,
    current: CurrentUser = Depends(require_superadmin),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationRead:
    """Fetch a tenant organization (superadmin only)."""
    return await service.get_org(current, org_id)


@router.put(
    "/{org_id}",
    response_model=OrganizationRead,
    summary="Update organization",
)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    current: CurrentUser = Depends(require_superadmin),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationRead:
    """Update tenant organization details (superadmin only)."""
    return await service.update_org(current, org_id, data)


@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization",
)
async def delete_organization(
    org_id: UUID,
    current: CurrentUser = Depends(require_superadmin),
    service: OrganizationService = Depends(get_organization_service),
) -> None:
    """Remove a tenant organization (superadmin only)."""
    await service.delete_org(current, org_id)
