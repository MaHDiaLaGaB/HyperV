from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException

from app.schemas.users import UserRead, UserUpdate, UserRolesUpdate, UserProvision  # drop UserCreate here (see note below)
from app.services.deps import get_user_service
from app.services.users import UserService
from app.security.clerk import get_current_user, role_required, CurrentUser

router = APIRouter()

# OPTIONAL: If you truly need to create local users manually, convert your old "register"
# into an admin-only "provision" endpoint that DOES NOT handle passwords.
# Example schema you might add later:


@router.post("/provision", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def provision_user(
    data: UserProvision,
    current: CurrentUser = Depends(role_required("superadmin")),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.provision_user(current, data)

@router.get("/", response_model=List[UserRead], summary="List users")
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> List[UserRead]:
    """
    List users within the caller's organization; superadmin sees all.
    """
    return await service.list_users(current, limit=limit, offset=offset)

@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user by ID",
    responses={404: {"description": "User not found"}},
)
async def get_user(
    user_id: UUID = Path(..., description="UUID of the user"),
    current: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Superadmin may fetch any user; others only users in their org (enforced in service).
    """
    return await service.get_user(current, user_id)

@router.put("/{user_id}", response_model=UserRead, summary="Update a user's profile")
async def update_user_profile(
    user_id: UUID = Path(..., description="UUID of the user"),
    data: UserUpdate = ...,  # body JSON
    current: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Users can update themselves; superadmin can update anyone.
    """
    if not (current["is_superadmin"] or current["id"] == str(user_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to update this profile",
        )
    return await service.update_profile(current, user_id, data)

@router.put("/{user_id}/roles", response_model=UserRead, summary="Assign roles to a user")
async def assign_user_roles(
    user_id: UUID = Path(..., description="UUID of the user"),
    data: UserRolesUpdate = ...,  # body JSON
    current: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Assign roles to a user: superadmin only (you can loosen to org admin if you want).
    """
    if not current["is_superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can assign roles",
        )
    return await service.assign_roles(current, user_id, data.role_ids)
