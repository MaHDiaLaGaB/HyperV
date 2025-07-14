from typing import List, Optional
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
from app.services.asset import AssetService
from app.services.deps import get_asset_service
from app.security.auth import current_active_user
from app.models.users.users import User
from app.schemas.enums import AssetType

router = APIRouter(
    dependencies=[Depends(current_active_user)]
)


@router.post(
    "/",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new asset",
)
async def upload_asset(
    asset_type: AssetType = Form(...),
    captured_at: Optional[datetime] = Form(None),
    footprint_wkt: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    service: AssetService = Depends(get_asset_service),
) -> AssetRead:
    # Parse JSON metadata
    try:
        meta_obj = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON for metadata",
        )
    create_dto = AssetCreate(
        organization_id=current_user.organization_id,
        asset_type=asset_type,
        file_path=file.filename,
        captured_at=captured_at.isoformat() if captured_at else None,
        footprint_wkt=footprint_wkt,
        metadata=meta_obj,
    )
    return await service.upload(
        current_user.organization_id,
        create_dto,
        file,
    )


@router.get(
    "/",
    response_model=List[AssetRead],
    summary="List all assets for organization",
)
async def list_assets(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    service: AssetService = Depends(get_asset_service),
    current_user: User = Depends(current_active_user),
) -> List[AssetRead]:
    return await service.list_assets(
        current_user.organization_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Get an asset by ID",
    responses={404: {"description": "Asset not found"}},
)
async def get_asset(
    asset_id: int = Path(..., ge=1),
    service: AssetService = Depends(get_asset_service),
    current_user: User = Depends(current_active_user),
) -> AssetRead:
    return await service.get_asset(
        current_user.organization_id,
        asset_id,
    )