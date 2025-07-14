from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from pydantic import EmailStr, BaseModel
from uuid import UUID
from .base import IDMixin, TimestampMixin


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    organization_id: UUID
    is_superuser: bool = False
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserRolesUpdate(BaseModel):
    role_ids: List[UUID]


class UserRead(IDMixin, TimestampMixin, UserBase):
    role_ids: List[UUID] = []
    permission_ids: List[UUID] = []

    class Config:
        from_attributes = True
