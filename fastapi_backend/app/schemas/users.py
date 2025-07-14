from __future__ import annotations
from typing import List, Optional
from pydantic import EmailStr, BaseModel
from uuid import UUID
from .base import IDMixin, TimestampMixin


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    organization_id: int
    is_superuser: bool = False
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserRolesUpdate(BaseModel):
    role_ids: List[int]


class UserRead(IDMixin, TimestampMixin, UserBase):
    id: UUID  # FastAPI‑Users UUID primary key
    role_ids: List[int] = []
    permission_ids: List[int] = []

    class Config:
        from_attributes = True
