from __future__ import annotations
from typing import List
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.permissions.permission import Permission
from app.models.users.organization import Organization


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    organization = relationship("Organization", back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    users = relationship("User", secondary="user_roles", back_populates="roles")

    __table_args__ = (UniqueConstraint("name", "organization_id", name="uq_role_org"),)
