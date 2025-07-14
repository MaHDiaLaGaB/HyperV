from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from .base import IDMixin, TimestampMixin


class PipelineBase(BaseModel):
    organization_id: int
    name: str
    length_km: float = Field(gt=0)


class PipelineCreate(PipelineBase):
    geom_wkt: Optional[str] = None  # Well‑Known Text


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    length_km: Optional[float] = None
    geom_wkt: Optional[str] = None


class PipelineRead(IDMixin, TimestampMixin, PipelineBase):
    geom_wkt: Optional[str]

    class Config:
        from_attributes = True
