from __future__ import annotations
from shapely import wkt
from fastapi import HTTPException, status
from app.schemas import PipelineCreate, PipelineRead
from app.repositories import PipelineRepository
from .base import BaseService

class PipelineService(BaseService[PipelineRepository]):
    async def create_pipeline(self, data: PipelineCreate) -> PipelineRead:
        geom = None
        if data.geom_wkt:
            try:
                geom_obj = wkt.loads(data.geom_wkt)
                if not geom_obj.is_valid:
                    raise ValueError
                geom = f"SRID=4326;{data.geom_wkt}"
            except Exception:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid WKT geometry")
        pipeline_db = self.repo.model(
            organization_id=data.organization_id,
            name=data.name,
            length_km=data.length_km,
            geom=geom,
        )
        await self.repo.create(pipeline_db)
        return PipelineRead.model_validate(pipeline_db)