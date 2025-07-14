from __future__ import annotations
from shapely import wkt
from fastapi import HTTPException, status

from app.schemas.pipeline import (
    PipelineCreate,
    PipelineRead,
    PipelineUpdate,
)
from app.repositories import PipelineRepository
from .base import BaseService


class PipelineService(BaseService[PipelineRepository]):
    """
    Service for managing Pipeline entities, scoped to an organization.
    """

    async def create_pipeline(
        self,
        org_id: int,
        data: PipelineCreate,
    ) -> PipelineRead:
        # Validate and convert WKT geometry
        geom = None
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
        # Persist pipeline
        pipeline = self.repo.model(
            organization_id=org_id,
            name=data.name,
            length_km=data.length_km,
            geom=geom,
        )
        await self.repo.create(pipeline)
        return PipelineRead.model_validate(pipeline)

    async def list_pipelines(
        self,
        org_id: int,
    ) -> list[PipelineRead]:
        items = await self.repo.list(
            filters=[self.repo.model.organization_id == org_id]
        )
        return [PipelineRead.model_validate(p) for p in items]

    async def get_pipeline(
        self,
        org_id: int,
        pipeline_id: int,
    ) -> PipelineRead:
        pipeline = await self.repo.get_in_org(org_id, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found in this organization",
            )
        return PipelineRead.model_validate(pipeline)

    async def update_pipeline(
        self,
        org_id: int,
        pipeline_id: int,
        data: PipelineUpdate,
    ) -> PipelineRead:
        pipeline = await self.repo.get_in_org(org_id, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found in this organization",
            )
        update_data = data.model_dump(exclude_none=True)
        # Handle geom update
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
        return PipelineRead.model_validate(updated)

    async def delete_pipeline(
        self,
        org_id: int,
        pipeline_id: int,
    ) -> None:
        pipeline = await self.repo.get_in_org(org_id, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found in this organization",
            )
        await self.repo.delete(pipeline)
