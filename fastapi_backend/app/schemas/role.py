from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
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


class RolePermissionsUpdate(BaseModel):
    permission_ids: List[int] = Field(
        ...,
        min_items=1,
        description="List of permission IDs to assign to this role (replaces any existing assignments)",
    )

    class Config:
        json_schema_extra = {"example": {"permission_ids": [1, 2, 3]}}


class RoleRead(IDMixin, TimestampMixin, RoleBase):
    permission_ids: List[int]

    class Config:
        from_attributes = True
