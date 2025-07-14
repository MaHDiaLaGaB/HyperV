from __future__ import annotations
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from .base import IDMixin, TimestampMixin
from .enums import EventType


class EventBase(BaseModel):
    organization_id: UUID
    event_type: EventType
    severity: Optional[int] = Field(None, ge=1, le=5)
    description: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None


class EventCreate(EventBase):
    location_wkt: Optional[str] = None


class EventUpdate(BaseModel):
    severity: Optional[int] = None
    description: Optional[str] = None


class EventRead(IDMixin, TimestampMixin, EventBase):
    detected_at: str  # ISO date‑time
    location_wkt: Optional[str]

    class Config:
        from_attributes = True
