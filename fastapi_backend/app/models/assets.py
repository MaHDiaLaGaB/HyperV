from __future__ import annotations
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Dict, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from app.db.base import Base
from app.schemas.enums import AssetType
import datetime as dt

if TYPE_CHECKING:
    from app.models.users.organization import Organization  # noqa: F401
    from app.models.events import Event  # noqa: F401


class Asset(Base):
    __tablename__ = "assets"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    captured_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))
    footprint: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    asset_metadata: Mapped[Optional[Dict]] = mapped_column(JSON)

    organization: Mapped["Organization"] = relationship(
        back_populates="assets"
    )  # noqa: F821
    events: Mapped[List["Event"]] = relationship(back_populates="asset")  # noqa: F821
