from __future__ import annotations
from app.models import Organization
from .base import AsyncRepository, AsyncSession

class OrganizationRepository(AsyncRepository[Organization]):
    model = Organization
