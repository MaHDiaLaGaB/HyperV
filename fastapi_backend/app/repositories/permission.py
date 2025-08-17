from __future__ import annotations
from app.models import Permission
from .base import AsyncRepository


class PermissionRepository(AsyncRepository[Permission]):
    model = Permission
