from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, status

from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineUpdate
from app.services.deps import get_pipeline_service
from app.services.pipeline import PipelineService
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post(
    "/",
    response_model=PipelineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pipeline",
)
async def create_pipeline(
    data: PipelineCreate,
    service: PipelineService = Depends(get_pipeline_service),
    current: CurrentUser = Depends(get_current_user),
) -> PipelineRead:
    """
    Register a new pipeline.
    Superadmins may specify `organization_id` in payload to target any tenant;
    others are scoped to their own org (enforced in service).
    """
    return await service.create_pipeline(current, data)


@router.get("/", response_model=List[PipelineRead], summary="List pipelines")
async def list_pipelines(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    service: PipelineService = Depends(get_pipeline_service),
    current: CurrentUser = Depends(get_current_user),
) -> List[PipelineRead]:
    """Retrieve pipelines scoped to your organization, or all if superadmin."""
    return await service.list_pipelines(current, limit=limit, offset=offset)


@router.get(
    "/{pipeline_id}",
    response_model=PipelineRead,
    summary="Get a pipeline by ID",
    responses={404: {"description": "Pipeline not found"}},
)
async def get_pipeline(
    pipeline_id: UUID = Path(..., description="ID of the pipeline"),
    service: PipelineService = Depends(get_pipeline_service),
    current: CurrentUser = Depends(get_current_user),
) -> PipelineRead:
    """Fetch a single pipeline."""
    return await service.get_pipeline(current, pipeline_id)


@router.patch(
    "/{pipeline_id}",
    response_model=PipelineRead,
    summary="Update pipeline details",
)
async def update_pipeline(
    pipeline_id: UUID,
    data: PipelineUpdate,
    service: PipelineService = Depends(get_pipeline_service),
    current: CurrentUser = Depends(get_current_user),
) -> PipelineRead:
    """Modify name, length, or geometry of a pipeline."""
    return await service.update_pipeline(current, pipeline_id, data)


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pipeline",
)
async def delete_pipeline(
    pipeline_id: UUID,
    service: PipelineService = Depends(get_pipeline_service),
    current: CurrentUser = Depends(get_current_user),
) -> None:
    """Remove a pipeline."""
    await service.delete_pipeline(current, pipeline_id)
