from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.deps import get_event_service
from app.services.event import EventService
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.post(
    "/",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new event",
)
async def ingest_event(
    data: EventCreate,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(current_active_user),
) -> EventRead:
    """Create a new event and trigger its initial alert."""
    return await service.ingest(current_user.organization_id, data)


@router.get(
    "/", response_model=List[EventRead], summary="List all events for organization"
)
async def list_events(
    limit: int = Query(100, ge=1, le=1000, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(current_active_user),
) -> List[EventRead]:
    """Retrieve events with related asset and pipeline info."""
    # Note: pagination not wired into repo.list_with_related by default
    events = await service.list_events(current_user.organization_id)
    return events[offset : offset + limit]


@router.get(
    "/{event_id}",
    response_model=EventRead,
    summary="Get an event by ID",
    responses={404: {"description": "Event not found in organization"}},
)
async def get_event(
    event_id: int = Path(..., description="ID of the event"),
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(current_active_user),
) -> EventRead:
    """Fetch a single event."""
    return await service.get_event(current_user.organization_id, event_id)


@router.patch(
    "/{event_id}", response_model=EventRead, summary="Update an event's details"
)
async def update_event(
    event_id: int,
    data: EventUpdate,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(current_active_user),
) -> EventRead:
    """Modify event severity or description."""
    return await service.update_event(current_user.organization_id, event_id, data)


@router.post(
    "/{event_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge all alerts for an event",
)
async def acknowledge_event(
    event_id: int,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(current_active_user),
) -> None:
    """Mark all alerts related to this event as acknowledged."""
    await service.acknowledge(current_user.organization_id, event_id)
