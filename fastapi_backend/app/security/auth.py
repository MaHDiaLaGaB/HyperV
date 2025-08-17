from typing import Optional
from fastapi_users.authentication import JWTStrategy
from app.core.config import settings


def get_jwt_strategy() -> JWTStrategy:
    """Return the JWT strategy for authentication."""
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)