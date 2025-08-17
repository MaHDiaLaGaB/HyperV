# app/routes/reports.py

from typing import List
from uuid import UUID
from pathlib import Path as FilePath

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    Query,
    Path,
    status,
    HTTPException,
)
from fastapi.responses import FileResponse

from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.services.report import ReportService
from app.services.deps import get_report_service
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter()


@router.post(
    "/",
    response_model=ReportRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a new report",
)
async def generate_report(
    data: ReportCreate,
    background: BackgroundTasks,
    current: CurrentUser = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    return await service.generate(current, data, background)


@router.get(
    "/",
    response_model=List[ReportRead],
    summary="List reports",
)
async def list_reports(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> List[ReportRead]:
    return await service.list_reports(current, limit=limit, offset=offset)


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Get a report by ID",
    responses={404: {"description": "Report not found"}},
)
async def get_report(
    report_id: UUID = Path(..., description="Report ID"),
    current: CurrentUser = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    return await service.get_report(current, report_id)


@router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    summary="Download report PDF",
    responses={404: {"description": "Report not found"}},
)
async def download_report(
    report_id: UUID = Path(..., description="Report ID"),
    current: CurrentUser = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> FileResponse:
    rpt = await service.get_report(current, report_id)
    if not rpt.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not yet generated"
        )
    return FileResponse(path=rpt.file_path, filename=FilePath(rpt.file_path).name)


@router.patch(
    "/{report_id}",
    response_model=ReportRead,
    summary="Update report summary",
)
async def update_report_summary(
    report_id: UUID,
    data: ReportUpdate,
    current: CurrentUser = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    return await service.update_summary(current, report_id, data)
