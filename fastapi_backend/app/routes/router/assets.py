from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Path,
    status,
)

from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.enums import AssetType
from app.services.asset import AssetService
from app.services.deps import get_asset_service
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.post(
    "/",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new asset",
)
async def upload_asset(
    asset_type: AssetType = Form(..., description="Asset type enum value"),
    organization_id: Optional[UUID] = Form(
        None, description="Target organization id (superuser only)"
    ),
    captured_at: Optional[datetime] = Form(None, description="ISO8601 timestamp"),
    footprint_wkt: Optional[str] = Form(None, description="WKT POLYGON string"),
    metadata: Optional[str] = Form(None, description="JSON-encoded metadata"),
    file: UploadFile = File(..., description="Binary asset file"),
    current_user: User = Depends(current_active_user),
    service: AssetService = Depends(get_asset_service),
) -> AssetRead:
    """Upload a binary asset with metadata and WKT footprint."""
    # Determine target org: superusers may override
    if current_user.is_superuser and organization_id is not None:
        target_org = organization_id
    else:
        target_org = current_user.organization_id

    try:
        meta_obj = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON for metadata",
        )

    create_dto = AssetCreate(
        organization_id=target_org,
        asset_type=asset_type,
        file_path=file.filename,
        captured_at=captured_at.isoformat() if captured_at else None,
        footprint_wkt=footprint_wkt,
        metadata=meta_obj,
    )
    return await service.upload(current_user, create_dto, file)


@router.get(
    "/",
    response_model=List[AssetRead],
    summary="List assets",
)
async def list_assets(
    limit: int = Query(100, ge=1, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(current_active_user),
    service: AssetService = Depends(get_asset_service),
) -> List[AssetRead]:
    """Retrieve assets scoped to your organization or all if superuser."""
    return await service.list_assets(current_user, limit=limit, offset=offset)


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Get an asset by ID",
    responses={404: {"description": "Asset not found"}},
)
async def get_asset(
    asset_id: UUID = Path(..., ge=1),
    current_user: User = Depends(current_active_user),
    service: AssetService = Depends(get_asset_service),
) -> AssetRead:
    """Fetch a single asset by ID, respecting superuser scope."""
    return await service.get_asset(current_user, asset_id)
