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
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter(
    dependencies=[Depends(current_active_user)],
)


@router.post(
    "/",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    data: OrganizationCreate,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(current_active_user),
) -> OrganizationRead:
    """Create a new tenant organization (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return await service.create_org(current_user=current_user, data=data)


@router.get(
    "/", response_model=List[OrganizationRead], summary="List all organizations"
)
async def list_organizations(
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(current_active_user),
) -> List[OrganizationRead]:
    """Retrieve all tenant organizations (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return await service.list_orgs(current_user=current_user)


@router.get(
    "/{org_id}",
    response_model=OrganizationRead,
    summary="Get organization by ID",
    responses={404: {"description": "Organization not found"}},
)
async def get_organization(
    org_id: UUID,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(current_active_user),
) -> OrganizationRead:
    """Fetch a tenant organization (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return await service.get_org(current_user, org_id)


@router.put("/{org_id}", response_model=OrganizationRead, summary="Update organization")
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(current_active_user),
) -> OrganizationRead:
    """Update tenant organization details (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return await service.update_org(current_user, org_id, data)


@router.delete(
    "/{org_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete organization"
)
async def delete_organization(
    org_id: UUID,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(current_active_user),
) -> None:
    """Remove a tenant organization (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    await service.delete_org(current_user, org_id)
