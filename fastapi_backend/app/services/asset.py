from __future__ import annotations
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException, status

from app.schemas.asset import AssetCreate, AssetRead
from app.repositories import AssetRepository
from .base import BaseService


class AssetService(BaseService[AssetRepository]):
    """
    Service for managing Asset uploads and retrievals, scoped to an organization.
    """
    async def upload(
        self,
        org_id: int,
        data: AssetCreate,
        file: UploadFile,
    ) -> AssetRead:
        # Prepare storage path
        dest_dir = Path("/data/assets") / str(org_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / file.filename
        # Write file
        content = await file.read()
        dest.write_bytes(content)

        # Build DB record
        asset_db = self.repo.model(
            organization_id=org_id,
            asset_type=data.asset_type,
            file_path=str(dest),
            captured_at=data.captured_at,
            asset_metadata=data.metadata,
            footprint=f"SRID=4326;{data.footprint_wkt}" if data.footprint_wkt else None,
        )
        await self.repo.create(asset_db)
        validated: AssetRead = AssetRead.model_validate(asset_db)
        return validated

    async def list_assets(
        self,
        org_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[AssetRead]:
        rows = await self.repo.list_by_org(
            org_id,
            limit=limit,
            offset=offset,
        )
        return [AssetRead.model_validate(a) for a in rows]

    async def get_asset(
        self,
        org_id: int,
        asset_id: int,
    ) -> AssetRead:
        asset = await self.repo.get_in_org(org_id, asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found in this organization",
            )
        validated: AssetRead = AssetRead.model_validate(asset)
        return validated