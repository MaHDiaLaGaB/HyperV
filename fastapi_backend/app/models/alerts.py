from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import DateTime, ForeignKey
import datetime as dt
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.events import Event  # noqa: F401

class Alert(Base):
    __tablename__ = "alerts"

    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    sent_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False)
    acknowledged_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))
    recipient_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))

    event: Mapped["Event"] = relationship(back_populates="alerts")  # noqa: F821