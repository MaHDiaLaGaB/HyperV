from __future__ import annotations
from shapely import wkt
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineUpdate
from app.security.clerk import CurrentUser
from app.repositories import PipelineRepository
from .base import BaseService


class PipelineService(BaseService[PipelineRepository]):
    """
    Service for managing Pipeline entities,
    supporting both global superuser access and organization-scoped operations.
    """

    def __init__(
        self,
        repo: PipelineRepository,
        db: AsyncSession,
    ) -> None:
        super().__init__(repo, db)

    async def create_pipeline(
        self,
        current_user: CurrentUser,
        data: PipelineCreate,
    ) -> PipelineRead:
        """
        Create a new pipeline. Superusers may create in any org;
        regular users only in their own org.
        """
        # Determine organization context
        org_id = (
            data.organization_id
            if current_user["is_superadmin"]
            and getattr(data, "organization_id", None) is not None
            else current_user["organization_id"]
        )

        # Validate geometry
        geom: str | None = None
        if data.geom_wkt:
            try:
                geom_obj = wkt.loads(data.geom_wkt)
                if not geom_obj.is_valid:
                    raise ValueError("Invalid geometry")
                geom = f"SRID=4326;{data.geom_wkt}"
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid WKT geometry",
                )

        pipeline = self.repo.model(
            organization_id=org_id,
            name=data.name,
            length_km=data.length_km,
            geom=geom,
        )
        await self.repo.create(pipeline)
        validated: PipelineRead = PipelineRead.model_validate(pipeline)
        return validated

    async def list_pipelines(
        self,
        current_user: CurrentUser,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[PipelineRead]:
        """
        List pipelines. Superusers see all; org users see only theirs.
        """
        if current_user["is_superadmin"]:
            rows = await self.repo.list(limit=limit, offset=offset)  # type: ignore
        else:
            rows = await self.repo.list_by_org(
                current_user["organization_id"],
                limit=limit,
                offset=offset,
            )
        return [PipelineRead.model_validate(p) for p in rows]

    async def get_pipeline(
        self,
        current_user: CurrentUser,
        pipeline_id: UUID,
    ) -> PipelineRead:
        """
        Fetch a single pipeline by ID. Scope based on user role.
        """
        if current_user["is_superadmin"]:
            pipeline = await self.repo.get(pipeline_id)
        else:
            pipeline = await self.repo.get_in_org(
                current_user["organization_id"], pipeline_id
            )
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        validated: PipelineRead = PipelineRead.model_validate(pipeline)
        return validated

    async def update_pipeline(
        self,
        current_user: CurrentUser,
        pipeline_id: UUID,
        data: PipelineUpdate,
    ) -> PipelineRead:
        """
        Update a pipeline. Superusers may update any; org users only theirs.
        """
        if current_user["is_superadmin"]:
            pipeline = await self.repo.get(pipeline_id)
        else:
            pipeline = await self.repo.get_in_org(
                current_user["organization_id"], pipeline_id
            )
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        update_data = data.model_dump(exclude_none=True)
        if "geom_wkt" in update_data:
            try:
                geom_obj = wkt.loads(update_data.pop("geom_wkt"))
                if not geom_obj.is_valid:
                    raise ValueError
                update_data["geom"] = f"SRID=4326;{geom_obj.wkt}"
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid WKT geometry",
                )
        updated = await self.repo.update(pipeline, update_data)
        validated: PipelineRead = PipelineRead.model_validate(updated)
        return validated

    async def delete_pipeline(
        self,
        current_user: CurrentUser,
        pipeline_id: UUID,
    ) -> None:
        """
        Delete a pipeline. Superusers may delete any; org users only theirs.
        """
        if current_user["is_superadmin"]:
            pipeline = await self.repo.get(pipeline_id)
        else:
            pipeline = await self.repo.get_in_org(
                current_user["organization_id"], pipeline_id
            )
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        await self.repo.delete(pipeline)
