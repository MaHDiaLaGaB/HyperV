from __future__ import annotations
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import EventCreate, EventRead

from app.repositories import EventRepository, AlertRepository
from .base import BaseService

class EventService(BaseService[EventRepository]):
    def __init__(self, repo: EventRepository, alert_repo: AlertRepository, db: AsyncSession):
        super().__init__(repo, db)
        self.alert_repo = alert_repo

    async def ingest(self, org_id: int, data: EventCreate) -> EventRead:
        # Optional: validate WKT; For brevity assume correct
        event_db = self.repo.model(
            organization_id=org_id,
            event_type=data.event_type,
            severity=data.severity,
            description=data.description,
            pipeline_id=data.pipeline_id,
            asset_id=data.asset_id,
        )
        if data.location_wkt:
            event_db.location = f"SRID=4326;{data.location_wkt}"
        await self.repo.create(event_db)
        # Trigger alerts
        await self.alert_repo.create(self.alert_repo.model(
            organization_id=org_id,
            event_id=event_db.id,
        ))
        return EventRead.model_validate(event_db)

    async def acknowledge(self, org_id: int, event_id: int):
        event = await self.repo.get_in_org(org_id, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        for alert in event.alerts:
            alert.acknowledged_at = datetime.utcnow()
        await self._commit()