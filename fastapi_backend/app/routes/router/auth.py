from fastapi import APIRouter
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.security.auth import auth_backend, fastapi_users, AUTH_URL_PATH


router = APIRouter()


# JWT auth endpoints  (e.g. /auth/jwt/login, /auth/jwt/logout)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=f"/{AUTH_URL_PATH}/jwt",
    tags=["auth"],
)

# Registration (e.g. POST /auth/register)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)

# Reset password (e.g. POST /auth/reset-password)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)

# Verify user (e.g. GET /auth/verify?token=…)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)

# “/users” → list users, get by id, update, delete
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
