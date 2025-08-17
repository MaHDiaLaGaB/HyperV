from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin
from .enums import ClientType


class OrganizationBase(BaseModel):
    name: str
    slug: str
    client_type: ClientType
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass  # all fields required


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    client_type: Optional[ClientType] = None
    is_active: Optional[bool] = None


class OrganizationRead(IDMixin, TimestampMixin, OrganizationBase):
    class Config:
        from_attributes = True
