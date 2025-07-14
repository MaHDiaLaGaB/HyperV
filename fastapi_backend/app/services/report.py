from __future__ import annotations
import tempfile
from pathlib import Path
from typing import List
from fastapi import BackgroundTasks, HTTPException, status

from app.schemas.report import (
    ReportCreate,
    ReportRead,
    ReportUpdate,
)
from app.repositories import ReportRepository
from .base import BaseService


class ReportService(BaseService[ReportRepository]):
    """
    Service for managing Report entities and generating PDFs, scoped to an organization.
    """

    async def generate(
        self,
        org_id: int,
        data: ReportCreate,
        background: BackgroundTasks,
    ) -> ReportRead:
        # Enforce org scope
        report_db = self.repo.model(
            organization_id=org_id,
            frequency=data.frequency,
            period_start=data.period_start,
            period_end=data.period_end,
            file_path=data.file_path,
            summary=data.summary,
        )
        # Save DB row without commit; PDF will be rendered in background
        await self.repo.create(report_db, commit=False)
        background.add_task(self._render_pdf, report_db)
        return ReportRead.model_validate(report_db)

    async def list_reports(
        self,
        org_id: int,
    ) -> List[ReportRead]:
        items = await self.repo.list_by_org(org_id)
        return [ReportRead.model_validate(r) for r in items]

    async def get_report(
        self,
        org_id: int,
        report_id: int,
    ) -> ReportRead:
        report = await self.repo.get_in_org(org_id, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found in this organization",
            )
        return ReportRead.model_validate(report)

    async def update_summary(
        self,
        org_id: int,
        report_id: int,
        data: ReportUpdate,
    ) -> ReportRead:
        report = await self.repo.get_in_org(org_id, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found in this organization",
            )
        report.summary = data.summary
        await self._commit()
        return ReportRead.model_validate(report)

    async def _render_pdf(self, report_db):
        # TODO: integrate real rendering (wkhtmltopdf/GIS libs)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        Path(temp.name).write_text("Report placeholder PDF")
        report_db.file_path = temp.name
        await self._commit()
