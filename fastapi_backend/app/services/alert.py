from __future__ import annotations
from datetime import datetime as dt
from typing import List
from fastapi import HTTPException, status
from app.schemas import AlertRead
from app.repositories import AlertRepository
from .base import BaseService

class AlertService(BaseService[AlertRepository]):
    async def list_unack(self, org_id: int) -> List[AlertRead]:
        alerts = await self.repo.list_by_org(org_id, self.repo.model.acknowledged_at.is_(None))
        return [AlertRead.model_validate(a) for a in alerts]

    async def acknowledge(self, org_id: int, alert_id: int):
        alert = await self.repo.get_in_org(org_id, alert_id)
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        alert.acknowledged_at = dt.utcnow()
        await self._commit()