from __future__ import annotations
from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.repositories import EventRepository, AlertRepository
from .base import BaseService


class EventService(BaseService[EventRepository]):
    """
    Service for managing Event entities and related alerts, scoped to an organization.
    """

    def __init__(
        self,
        repo: EventRepository,
        alert_repo: AlertRepository,
        db: AsyncSession,
    ):
        super().__init__(repo, db)
        self.alert_repo = alert_repo

    async def ingest(
        self,
        org_id: int,
        data: EventCreate,
    ) -> EventRead:
        # Persist event
        event = self.repo.model(
            organization_id=org_id,
            event_type=data.event_type,
            severity=data.severity,
            description=data.description,
            pipeline_id=data.pipeline_id,
            asset_id=data.asset_id,
        )
        if data.location_wkt:
            event.location = f"SRID=4326;{data.location_wkt}"
        await self.repo.create(event)
        # Trigger initial alert
        await self.alert_repo.create(
            self.alert_repo.model(
                organization_id=org_id,
                event_id=event.id,
            )
        )
        return EventRead.model_validate(event)

    async def list_events(
        self,
        org_id: int,
    ) -> List[EventRead]:
        # Eager load asset and pipeline
        events = await self.repo.list_with_related(org_id)
        return [EventRead.model_validate(e) for e in events]

    async def get_event(
        self,
        org_id: int,
        event_id: int,
    ) -> EventRead:
        event = await self.repo.get_in_org(org_id, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found in this organization",
            )
        return EventRead.model_validate(event)

    async def update_event(
        self,
        org_id: int,
        event_id: int,
        data: EventUpdate,
    ) -> EventRead:
        event = await self.repo.get_in_org(org_id, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found in this organization",
            )
        update_data = data.model_dump(exclude_none=True)
        updated = await self.repo.update(event, update_data)
        valedated: EventRead = EventRead.model_validate(updated)
        return valedated

    async def acknowledge(
        self,
        org_id: int,
        event_id: int,
    ) -> None:
        # Mark all alerts for this event as acknowledged
        event = await self.repo.get_in_org(org_id, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found in this organization",
            )
        for alert in event.alerts:
            alert.acknowledged_at = datetime.utcnow()
        await self._commit()
