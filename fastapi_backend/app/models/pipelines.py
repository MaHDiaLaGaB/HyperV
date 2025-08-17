from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Float, ForeignKey, String, JSON
from app.db.base import Base
from app.models.events import Event  # noqa: F401

if TYPE_CHECKING:
    from app.models.users.organization import Organization  # noqa: F401


class Pipeline(Base):
    __tablename__ = "pipelines"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String, nullable=False
    )  # store name in JSON or String as needed
    length_km: Mapped[float] = mapped_column(Float, nullable=False)
    geom_geojson: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)

    organization: Mapped["Organization"] = relationship(
        back_populates="pipelines"
    )  # noqa: F821
    events: Mapped[List["Event"]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan"
    )  # noqa: F821


"""
from geoalchemy2.functions import ST_AsText

# Get geometry as WKT string
result = await session.execute(
    select(Pipeline, ST_AsText(Pipeline.geom).label("wkt"))
"""
