from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin
from .enums import AssetType


class AssetBase(BaseModel):
    organization_id: int
    asset_type: AssetType
    file_path: str
    captured_at: Optional[str] = None  # ISO date‑time


class AssetCreate(AssetBase):
    footprint_wkt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetUpdate(BaseModel):
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetRead(IDMixin, TimestampMixin, AssetBase):
    footprint_wkt: Optional[str]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True
