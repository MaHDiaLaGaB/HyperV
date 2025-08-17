from __future__ import annotations
from datetime import datetime as dt
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.alert import AlertRead
from app.security.clerk import CurrentUser
from app.repositories import AlertRepository
from .base import BaseService


class AlertService(BaseService[AlertRepository]):
    """
    Service for managing Alert entities, supporting both global superuser
    access and organization-scoped operations.
    """

    async def list_unack(
        self,
        current_user: CurrentUser,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[AlertRead]:
        """
        List all unacknowledged alerts.
        - Superusers see all unacknowledged alerts.
        - Organization users see only their org's unacknowledged alerts.
        """
        if current_user["is_superadmin"]:
            # Global: list all where acknowledged_at is null
            alerts = await self.repo.list(
                filters=[self.repo.model.acknowledged_at.is_(None)],
                limit=limit,
                offset=offset,
            )
        else:
            alerts = await self.repo.list_by_org(
                current_user["organization_id"],
                filters=[self.repo.model.acknowledged_at.is_(None)],
                limit=limit,
                offset=offset,
            )
        return [AlertRead.model_validate(a) for a in alerts]

    async def acknowledge(
        self,
        current_user: CurrentUser,
        alert_id: UUID,
    ) -> None:
        """
        Acknowledge a single alert.
        - Superusers can acknowledge any alert.
        - Organization users can only acknowledge alerts in their org.
        """
        # Fetch alert based on role
        if current_user["is_superadmin"]:
            alert = await self.repo.get(alert_id)
        else:
            alert = await self.repo.get_in_org(current_user["organization_id"], alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )
        alert.acknowledged_at = dt.utcnow()
        await self._commit()
