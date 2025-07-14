from __future__ import annotations
from pathlib import Path
from typing import List
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.asset import AssetCreate, AssetRead
from app.repositories import AssetRepository
from app.models.users.users import User
from .base import BaseService


class AssetService(BaseService[AssetRepository]):
    """
    Service for managing Asset uploads and retrievals,
    supporting both global superusers and org-scoped users.
    """

    async def upload(
        self,
        current_user: User,
        data: AssetCreate,
        file: UploadFile,
    ) -> AssetRead:
        """
        Upload a file and create an asset record.
        - Superusers may upload into any organization by specifying data.organization_id.
        - Regular users only upload into their own organization.
        """
        # Determine target org
        if current_user.is_superuser:
            org_id = data.organization_id
        else:
            org_id = current_user.organization_id
            if data.organization_id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not permitted to upload to this organization",
                )

        # Prepare storage path
        dest_dir = Path("/data/assets") / str(org_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / file.filename
        content = await file.read()
        dest.write_bytes(content)

        # Create DB record
        asset_db = self.repo.model(
            organization_id=org_id,
            asset_type=data.asset_type,
            file_path=str(dest),
            captured_at=data.captured_at,
            asset_metadata=data.metadata,
            footprint=(
                f"SRID=4326;{data.footprint_wkt}" if data.footprint_wkt else None
            ),
        )
        await self.repo.create(asset_db)
        validated: AssetRead = AssetRead.model_validate(asset_db)
        return validated

    async def list_assets(
        self,
        current_user: User,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[AssetRead]:
        """
        List assets. Superusers see all; others see org-scoped.
        """
        if current_user.is_superuser:
            rows = await self.repo.list(limit=limit, offset=offset)
        else:
            rows = await self.repo.list_by_org(
                current_user.organization_id,
                limit=limit,
                offset=offset,
            )
        return [AssetRead.model_validate(a) for a in rows]

    async def get_asset(
        self,
        current_user: User,
        asset_id: UUID,
    ) -> AssetRead:
        """
        Get an asset by ID. Superusers can fetch any; others only their org.
        """
        if current_user.is_superuser:
            asset = await self.repo.get(asset_id)
        else:
            asset = await self.repo.get_in_org(current_user.organization_id, asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found",
            )
        validated: AssetRead = AssetRead.model_validate(asset)
        return validated
