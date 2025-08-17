from __future__ import annotations
from typing import List, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.permissions.roles import Role

class User(Base):
    __tablename__ = "user"  # keep same name your code expects

    # Link to Clerk user
    clerk_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Required fields based on database schema
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization = relationship("Organization", back_populates="users")
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("clerk_user_id", name="uq_user_clerk_user_id"),
    )
