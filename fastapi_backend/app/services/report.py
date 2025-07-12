from __future__ import annotations
import tempfile
from pathlib import Path
from fastapi import BackgroundTasks
from app.schemas import ReportCreate, ReportRead
from app.repositories import ReportRepository
from .base import BaseService

class ReportService(BaseService[ReportRepository]):
    async def generate(self, data: ReportCreate, background: BackgroundTasks) -> ReportRead:
        # Offload heavy PDF/GIS rendering
        report_db = self.repo.model(**data.model_dump())
        await self.repo.create(report_db, commit=False)  # commit later in bg
        background.add_task(self._render_pdf, report_db)
        return ReportRead.model_validate(report_db)

    async def _render_pdf(self, report_db):
        # TODO: hook to wkhtmltopdf or GIS renderer
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        Path(temp.name).write_text("Report placeholder")
        report_db.file_path = temp.name
        await self._commit()
