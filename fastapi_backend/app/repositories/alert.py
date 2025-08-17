from __future__ import annotations
from app.models import Alert
from .base import AsyncRepository
from .mixins import OrgFilterMixin


class AlertRepository(OrgFilterMixin, AsyncRepository[Alert]):
    model = Alert
