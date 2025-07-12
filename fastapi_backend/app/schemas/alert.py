from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin


class AlertBase(BaseModel):
    organization_id: int
    event_id: int
    recipient_user_id: Optional[int] = None


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    acknowledged_at: Optional[str] = None  # ISO date‑time


class AlertRead(IDMixin, TimestampMixin, AlertBase):
    sent_at: str
    acknowledged_at: Optional[str]

    class Config:
        from_attributes = True
