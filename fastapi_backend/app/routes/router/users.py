from typing import List
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
)

from app.services.deps import get_user_service
from app.services.users import UserService
from app.schemas.users import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserRolesUpdate,
)
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter()


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    Public endpoint: register a new user.
    """
    return await service.register(data)


@router.get("/", response_model=List[UserRead], summary="List users for organization")
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
) -> List[UserRead]:
    """
    List all users within the current user's organization.
    """
    return await service.list_users(
        current_user.organization_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user by ID",
    responses={404: {"description": "User not found in organization"}},
)
async def get_user(
    user_id: UUID = Path(..., description="UUID of the user"),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
) -> UserRead:
    """
    Fetch a single user with roles and permissions.
    """
    return await service.get_user(
        current_user.organization_id,
        user_id,
    )


@router.put("/{user_id}", response_model=UserRead, summary="Update a user's profile")
async def update_user_profile(
    user_id: UUID,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
) -> UserRead:
    """
    Users may update their own profile; superusers may update any user.
    """
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to update this profile",
        )
    return await service.update_profile(
        current_user.organization_id,
        user_id,
        data,
    )


@router.put(
    "/{user_id}/roles", response_model=UserRead, summary="Assign roles to a user"
)
async def assign_user_roles(
    user_id: UUID,
    data: UserRolesUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
) -> UserRead:
    """
    Superusers may assign roles to users within their organization.
    Replaces existing role assignments.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can assign roles",
        )
    return await service.assign_roles(
        current_user.organization_id,
        user_id,
        data.role_ids,
    )
