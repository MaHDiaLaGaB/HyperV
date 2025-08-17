from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.security.clerk import CurrentUser


@dataclass(frozen=True)
class UserContext:
    """Lightweight, service-friendly view of the current user."""
    user_id: UUID
    organization_id: Optional[UUID]
    is_superadmin: bool


def ctx_from_current_user(cu: CurrentUser) -> UserContext:
    """
    Convert the Clerk-derived CurrentUser (TypedDict of strings) into a typed context.
    - cu["id"] and cu["organization_id"] are strings (UUIDs) or None.
    """
    user_id = UUID(cu["id"])
    org_id = UUID(cu["organization_id"]) if cu.get("organization_id") else None
    return UserContext(
        user_id=user_id,
        organization_id=org_id,
        is_superadmin=bool(cu.get("is_superadmin", False)),
    )
