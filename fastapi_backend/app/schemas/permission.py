from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin


class PermissionBase(BaseModel):
    code: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    description: Optional[str] = None


class PermissionRead(IDMixin, TimestampMixin, PermissionBase):
    class Config:
        from_attributes = True
