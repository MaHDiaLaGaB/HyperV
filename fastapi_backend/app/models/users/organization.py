from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as SQLEnum
from app.schemas.enums import ClientType
from app.db.base import Base
from app.models.pipelines import Pipeline
from app.models.events import Event
from app.models.assets import Asset
from app.models.reports import Report

if TYPE_CHECKING:
    from .users import User
    from app.models.permissions.roles import Role

class Organization(Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # NEW: link to Clerk organization (optional but recommended)
    clerk_org_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    client_type: Mapped[ClientType] = mapped_column(SQLEnum(ClientType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[List["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    pipelines: Mapped[List["Pipeline"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    events: Mapped[List["Event"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    assets: Mapped[List["Asset"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    roles: Mapped[List["Role"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    # Add a named unique constraint to match your Alembic migration
    __table_args__ = (
        UniqueConstraint("clerk_org_id", name="uq_org_clerk_org_id"),
    )
