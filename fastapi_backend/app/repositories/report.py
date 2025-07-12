from __future__ import annotations
from app.models import Report
from .base import AsyncRepository
from .mixins import OrgFilterMixin

class ReportRepository(OrgFilterMixin, AsyncRepository[Report]):
    model = Report
