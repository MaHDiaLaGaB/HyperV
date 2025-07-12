from __future__ import annotations
from pathlib import Path
from fastapi import UploadFile
from app.schemas import AssetCreate, AssetRead
from app.repositories import AssetRepository
from .base import BaseService

class AssetService(BaseService[AssetRepository]):
    async def upload(self, data: AssetCreate, file: UploadFile) -> AssetRead:
        dest = Path("/data/assets") / file.filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(await file.read())
        asset_db = self.repo.model(
            organization_id=data.organization_id,
            asset_type=data.asset_type,
            file_path=str(dest),
            captured_at=data.captured_at,
            metadata=data.metadata,
            footprint=f"SRID=4326;{data.footprint_wkt}" if data.footprint_wkt else None,
        )
        await self.repo.create(asset_db)
        return AssetRead.model_validate(asset_db)
