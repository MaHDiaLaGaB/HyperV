from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin
from .enums import ReportFrequency


class ReportBase(BaseModel):
    organization_id: int
    frequency: ReportFrequency
    period_start: str  # ISO date
    period_end: str
    file_path: str
    summary: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    summary: Optional[str] = None


class ReportRead(IDMixin, TimestampMixin, ReportBase):
    generated_at: str

    class Config:
        from_attributes = True
