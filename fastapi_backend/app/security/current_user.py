# app/security/current_user.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.deps import get_db
from app.models.users.users import User
from app.security.clerk import ClerkClaims, require_clerk_session
from app.schemas.users import CurrentUser

async def _auto_provision_user(db: AsyncSession, claims: ClerkClaims) -> User:
    clerk_user_id = claims["sub"]
    email = claims.get("email") or f"{clerk_user_id}@unknown.local"
    full_name = claims.get("name") or email.split("@")[0]

    user = User(
        clerk_user_id=clerk_user_id,
        email=email,
        full_name=full_name,
        hashed_password="",  # not used; Clerk manages auth
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def current_user(
    claims: ClerkClaims = Depends(require_clerk_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    clerk_user_id = claims["sub"]

    res = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user: Optional[User] = res.scalars().first()

    if not user:
        if settings.AUTO_PROVISION_USERS:
            user = await _auto_provision_user(db, claims)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not registered in this system",
            )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


def _serialize(user: User) -> CurrentUser:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "roles": [r.name for r in user.roles],  # purely from your DB
        "organization_id": str(user.organization_id) if user.organization_id else None,
    }

async def get_current_user(user: User = Depends(current_user)) -> CurrentUser:
    return _serialize(user)


def role_required(role_name: str, allow_superuser: bool = True):
    role_name_l = role_name.lower()

    async def _dep(user: User = Depends(current_user)) -> CurrentUser:
        if allow_superuser and user.is_superuser and user.clerk_user_id in settings.SUPERADMINS:
            return _serialize(user)
        if not any((r.name or "").lower() == role_name_l for r in user.roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return _serialize(user)

    return _dep

