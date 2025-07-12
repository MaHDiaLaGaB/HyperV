from __future__ import annotations
from app.models import Asset
from .base import AsyncRepository
from .mixins import OrgFilterMixin

class AssetRepository(OrgFilterMixin, AsyncRepository[Asset]):
    model = Asset