from __future__ import annotations
from typing import TYPE_CHECKING, List
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.permissions.roles import Role


class User(SQLAlchemyBaseUserTableUUID, Base):
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    full_name: Mapped[str] = mapped_column(String(255))
    organization = relationship("Organization", back_populates="users")

    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles", back_populates="users"
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
    )

Role.users = relationship(
    "User", secondary="user_roles", back_populates="roles", cascade="all"
)