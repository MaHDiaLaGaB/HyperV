from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, JSON
from app.db.base import Base
import datetime as dt
from app.schemas.enums import EventType
from app.models.assets import Asset  # noqa: F401
from app.models.alerts import Alert  # noqa: F401

if TYPE_CHECKING:
    from app.models.users.organization import Organization  # noqa: F401
    from app.models.pipelines import Pipeline  # noqa: F401


class Event(Base):
    __tablename__ = "events"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False)
    detected_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    severity: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)

    location_geojeson: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    pipeline_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pipelines.id", ondelete="SET NULL")
    )
    asset_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="events"
    )  # noqa: F821
    pipeline: Mapped[Optional["Pipeline"]] = relationship(
        back_populates="events"
    )  # noqa: F821
    asset: Mapped[Optional["Asset"]] = relationship(
        back_populates="events"
    )  # noqa: F821
    alerts: Mapped[List["Alert"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )  # noqa: F821
