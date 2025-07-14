from __future__ import annotations
from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.models.users.users import User
from app.repositories import EventRepository, AlertRepository
from .base import BaseService


class EventService(BaseService[EventRepository]):
    """
    Service for managing Event entities and related alerts,
    supporting both global superuser access and organization-scoped operations.
    """

    def __init__(
        self,
        repo: EventRepository,
        alert_repo: AlertRepository,
        db: AsyncSession,
    ) -> None:
        super().__init__(repo, db)
        self.alert_repo = alert_repo

    async def ingest(
        self,
        current_user: User,
        data: EventCreate,
    ) -> EventRead:
        """
        Ingest a new event. Superusers may specify data.organization_id;
        other users are scoped to their own organization.
        """
        # Determine target organization
        org_id = (
            data.organization_id
            if current_user.is_superuser and data.organization_id is not None
            else current_user.organization_id
        )

        # Create event
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
        alert = self.alert_repo.model(
            organization_id=org_id,
            event_id=event.id,
        )
        await self.alert_repo.create(alert)

        validated: EventRead = EventRead.model_validate(event)
        return validated

    async def list_events(
        self,
        current_user: User,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[EventRead]:
        """
        List events for organization or all if superuser.
        """
        if current_user.is_superuser:
            events = await self.repo.list_with_related(
                limit=limit, offset=offset  # type: ignore
            )
        else:
            events = await self.repo.list_with_related(
                current_user.organization_id,
                limit=limit,
                offset=offset,
            )
        return [EventRead.model_validate(e) for e in events]

    async def get_event(
        self,
        current_user: User,
        event_id: UUID,
    ) -> EventRead:
        """
        Fetch a single event by ID, respecting superuser scope.
        """
        event = (
            await self.repo.get(event_id)
            if current_user.is_superuser
            else await self.repo.get_in_org(current_user.organization_id, event_id)
        )
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        validated: EventRead = EventRead.model_validate(event)
        return validated

    async def update_event(
        self,
        current_user: User,
        event_id: UUID,
        data: EventUpdate,
    ) -> EventRead:
        """
        Update an event's fields. Superusers may update any event.
        """
        event = (
            await self.repo.get(event_id)
            if current_user.is_superuser
            else await self.repo.get_in_org(current_user.organization_id, event_id)
        )
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        update_data = data.model_dump(exclude_none=True)
        updated = await self.repo.update(event, update_data)
        validated: EventRead = EventRead.model_validate(updated)
        return validated

    async def acknowledge(
        self,
        current_user: User,
        event_id: UUID,
    ) -> None:
        """
        Acknowledge all alerts for an event. Superusers may acknowledge any event.
        """
        event = (
            await self.repo.get(event_id)
            if current_user.is_superuser
            else await self.repo.get_in_org(current_user.organization_id, event_id)
        )
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        for alert in event.alerts:
            alert.acknowledged_at = datetime.utcnow()
        await self._commit()
