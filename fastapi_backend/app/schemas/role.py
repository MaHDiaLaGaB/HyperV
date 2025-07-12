from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from .base import IDMixin, TimestampMixin


class RoleBase(BaseModel):
    name: str
    organization_id: int
    permission_ids: List[int] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleRead(IDMixin, TimestampMixin, RoleBase):
    permission_ids: List[int]

    class Config:
        from_attributes = True
