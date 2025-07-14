from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException

from app.schemas.role import RoleCreate, RoleRead, RolePermissionsUpdate
from app.services.deps import get_role_service
from app.services.role import RoleService
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter()


@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(current_active_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Create a role within your organization.
    Superusers may set `organization_id` in the payload to target any tenant;
    regular users will have roles created in their own org.
    """
    return await service.create_role(current_user, data)


@router.get(
    "/",
    response_model=List[RoleRead],
    summary="List roles",
)
async def list_roles(
    org_id: Optional[UUID] = Query(
        None, description="Organization ID to list roles for (required for superusers)"
    ),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    service: RoleService = Depends(get_role_service),
) -> List[RoleRead]:
    """
    List roles for your organization.
    Superusers must supply `?org_id=...` to list that tenant's roles.
    """
    return await service.list_roles(
        current_user, org_id=org_id, limit=limit, offset=offset
    )


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get a role by ID",
    responses={404: {"description": "Role not found"}},
)
async def get_role(
    role_id: UUID = Path(..., description="UUID of the role"),
    current_user: User = Depends(current_active_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Fetch a single role by its ID.
    Superusers may fetch any role; org users only their own.
    """
    return await service.get_role(current_user, role_id)


@router.patch(
    "/{role_id}/permissions",
    response_model=RoleRead,
    summary="Assign permissions to a role",
)
async def assign_role_permissions(
    role_id: UUID = Path(..., description="UUID of the role"),
    data: RolePermissionsUpdate = Depends(),
    current_user: User = Depends(current_active_user),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """
    Replace the set of permissions on a role.
    Superusers may update any role; org users only their own.
    """
    return await service.assign_permissions(current_user, role_id, data)
