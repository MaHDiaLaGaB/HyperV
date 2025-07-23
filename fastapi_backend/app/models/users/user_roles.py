from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    # id: Mapped[UUID] = mapped_column(
    #     UUID(as_uuid=True),
    #     primary_key=True,
    #     default=uuid4,
    #     nullable=False,
    # )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
