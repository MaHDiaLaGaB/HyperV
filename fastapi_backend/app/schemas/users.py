from __future__ import annotations
from typing import List, Optional, TypedDict
from uuid import UUID
from pydantic import EmailStr, BaseModel
from uuid import UUID
from .base import IDMixin, TimestampMixin

class CurrentUser(TypedDict):
    id: str                 # your local UUID (as str)
    clerk_user_id: str
    email: Optional[str]
    full_name: Optional[str]
    organization_id: Optional[str]
    org_role: Optional[str]
    org_slug: Optional[str]
    is_superadmin: bool
    permissions: List[str]

class UserProvision(BaseModel):
    clerk_user_id: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    organization_id: Optional[UUID] = None


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
