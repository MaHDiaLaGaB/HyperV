from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, status

from app.schemas.role import RoleCreate, RoleRead, RolePermissionsUpdate
from app.services.deps import get_role_service
from app.services.role import RoleService
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter()


@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    data: RoleCreate,
    current: CurrentUser = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Create a role within your organization.
    Superadmins may set `organization_id` in the payload to target any tenant;
    regular users create roles in their own org (enforced in service).
    """
    return await service.create_role(current, data)


@router.get(
    "/",
    response_model=List[RoleRead],
    summary="List roles",
)
async def list_roles(
    org_id: Optional[UUID] = Query(
        None, description="Organization ID to list roles for (required for superadmins)"
    ),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
) -> List[RoleRead]:
    """
    List roles for your organization.
    Superadmins must supply `?org_id=...` to list that tenant's roles.
    """
    return await service.list_roles(current, org_id=org_id, limit=limit, offset=offset)


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get a role by ID",
    responses={404: {"description": "Role not found"}},
)
async def get_role(
    role_id: UUID = Path(..., description="UUID of the role"),
    current: CurrentUser = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Fetch a single role by its ID.
    Superadmins may fetch any role; org users only their own (enforced in service).
    """
    return await service.get_role(current, role_id)


@router.patch(
    "/{role_id}/permissions",
    response_model=RoleRead,
    summary="Assign permissions to a role",
)
async def assign_role_permissions(
    role_id: UUID = Path(..., description="UUID of the role"),
    data: RolePermissionsUpdate = ...,
    current: CurrentUser = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Replace the set of permissions on a role.
    Superadmins may update any role; org users only their own (enforced in service).
    """
    return await service.assign_permissions(current, role_id, data)
