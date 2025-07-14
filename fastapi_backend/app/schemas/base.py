from __future__ import annotations
import datetime as dt
from pydantic import BaseModel, field_validator
from uuid import UUID


class IDMixin(BaseModel):
    id: UUID

    class Config:
        from_attributes = True  # Pydantic v2: ORM mode


class TimestampMixin(BaseModel):
    created_at: dt.datetime
    updated_at: dt.datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_tz_aware(cls, v: dt.datetime) -> dt.datetime:  # noqa: N805
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v

    class Config:
        from_attributes = True
