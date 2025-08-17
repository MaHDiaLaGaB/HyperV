from __future__ import annotations
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin


class AlertBase(BaseModel):
    organization_id: UUID
    event_id: UUID
    recipient_user_id: Optional[UUID] = None


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    acknowledged_at: Optional[str] = None  # ISO date‑time


class AlertRead(IDMixin, TimestampMixin, AlertBase):
    sent_at: str
    acknowledged_at: Optional[str]

    class Config:
        from_attributes = True
