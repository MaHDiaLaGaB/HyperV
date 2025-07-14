from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import String, Text, DateTime, Enum as SQLEnum, ForeignKey
from app.db.base import Base
import datetime as dt
from app.schemas.enums import ReportFrequency

if TYPE_CHECKING:
    from app.models.users.organization import Organization  # noqa: F401


class Report(Base):
    __tablename__ = "reports"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frequency: Mapped[ReportFrequency] = mapped_column(
        SQLEnum(ReportFrequency), nullable=False
    )
    period_start: Mapped[dt.date] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    period_end: Mapped[dt.date] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    generated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)

    organization: Mapped["Organization"] = relationship(
        back_populates="reports"
    )  # noqa: F821
