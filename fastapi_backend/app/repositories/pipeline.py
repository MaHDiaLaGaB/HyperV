from __future__ import annotations
from app.models import Pipeline
from .base import AsyncRepository
from .mixins import OrgFilterMixin


class PipelineRepository(OrgFilterMixin, AsyncRepository[Pipeline]):
    model = Pipeline
