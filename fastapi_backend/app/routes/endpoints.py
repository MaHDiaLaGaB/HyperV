from fastapi import APIRouter
from app.routes.router import items, auth

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(items.router, prefix="/items", tags=["items"])
