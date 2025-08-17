# app/services/report.py

from __future__ import annotations
import tempfile
from pathlib import Path
from typing import List
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status

from app.security.clerk import CurrentUser
from app.repositories import ReportRepository
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from .base import BaseService


class ReportService(BaseService[ReportRepository]):
    """
    Service for managing Report entities and generating PDFs,
    supporting both global superuser access and organization-scoped operations.
    """

    async def generate(
        self,
        current_user: CurrentUser,
        data: ReportCreate,
        background: BackgroundTasks,
    ) -> ReportRead:
        """
        Initiate report generation:
        - Superusers may specify data.organization_id; others use their org.
        - PDF rendering happens in background.
        """
        org_id = (
            data.organization_id
            if current_user["is_superadmin"]
            and getattr(data, "organization_id", None) is not None
            else current_user["organization_id"]
        )

        report_db = self.repo.model(
            organization_id=org_id,
            frequency=data.frequency,
            period_start=data.period_start,
            period_end=data.period_end,
            file_path=data.file_path,
            summary=data.summary,
        )
        await self.repo.create(report_db, commit=False)
        background.add_task(self._render_pdf, report_db)
        validated: ReportRead = ReportRead.model_validate(report_db)
        return validated

    async def list_reports(
        self,
        current_user: CurrentUser,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[ReportRead]:
        """
        List reports:
        - Superusers see all; org users see only theirs.
        """
        if current_user["is_superadmin"]:
            rows = await self.repo.list(limit=limit, offset=offset)  # type: ignore
        else:
            rows = await self.repo.list_by_org(
                current_user["organization_id"], limit=limit, offset=offset
            )
        return [ReportRead.model_validate(r) for r in rows]

    async def get_report(
        self,
        current_user: CurrentUser,
        report_id: UUID,
    ) -> ReportRead:
        """
        Fetch a single report by ID, respecting superuser scope.
        """
        if current_user["is_superadmin"]:
            rpt = await self.repo.get(report_id)
        else:
            rpt = await self.repo.get_in_org(current_user["organization_id"], report_id)
        if not rpt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )
        validated: ReportRead = ReportRead.model_validate(rpt)
        return validated

    async def update_summary(
        self,
        current_user: CurrentUser,
        report_id: UUID,
        data: ReportUpdate,
    ) -> ReportRead:
        """
        Update the summary text of a report.
        """
        if current_user["is_superadmin"]:
            rpt = await self.repo.get(report_id)
        else:
            rpt = await self.repo.get_in_org(current_user["organization_id"], report_id)
        if not rpt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )
        rpt.summary = data.summary
        await self._commit()
        validated: ReportRead = ReportRead.model_validate(rpt)
        return validated

    async def _render_pdf(self, report_db) -> None:
        """
        Background task to render PDF; stores the file path and commits.
        """
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        Path(temp.name).write_text("Report placeholder PDF")
        report_db.file_path = temp.name
        await self._commit()
