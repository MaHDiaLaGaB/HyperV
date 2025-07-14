from typing import List
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
from app.services.deps import get_report_service
from app.services.report import ReportService
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter(
    prefix="/reports", tags=["Reports"], dependencies=[Depends(current_active_user)]
)


@router.post(
    "/",
    response_model=ReportRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a new report",
)
async def generate_report(
    data: ReportCreate,
    background: BackgroundTasks,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(current_active_user),
) -> ReportRead:
    """Initiate report generation; PDF rendering runs in background."""
    return await service.generate(
        current_user.organization_id,
        data,
        background,
    )


@router.get(
    "/", response_model=List[ReportRead], summary="List all reports for organization"
)
async def list_reports(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(current_active_user),
) -> List[ReportRead]:
    """Retrieve reports scoped to the current user's organization."""
    reports = await service.list_reports(current_user.organization_id)
    return reports[offset : offset + limit]


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Get a report by ID",
    responses={404: {"description": "Report not found in organization"}},
)
async def get_report(
    report_id: int = Path(..., description="ID of the report"),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(current_active_user),
) -> ReportRead:
    """Fetch a single report record."""
    return await service.get_report(current_user.organization_id, report_id)


@router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    summary="Download the generated PDF for a report",
)
async def download_report(
    report_id: int = Path(..., description="ID of the report"),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(current_active_user),
) -> FileResponse:
    """Serve the PDF file for a completed report."""
    report = await service.get_report(current_user.organization_id, report_id)
    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not yet generated"
        )
    return FileResponse(path=report.file_path, filename=Path(report.file_path).name)


@router.patch(
    "/{report_id}", response_model=ReportRead, summary="Update report summary"
)
async def update_report_summary(
    report_id: int,
    data: ReportUpdate,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(current_active_user),
) -> ReportRead:
    """Modify the summary text of an existing report."""
    return await service.update_summary(
        current_user.organization_id,
        report_id,
        data,
    )
