from fastapi import APIRouter
from app.routes.router import (
    auth,
    users,
    organizations,
    roles,
    permissions,
    assets,
    events,
    reports,
    pipelines,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    organizations.router, prefix="/organizations", tags=["Organizations"]
)
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["Permissions"],
)
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
