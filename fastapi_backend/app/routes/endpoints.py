from fastapi import APIRouter
from app.routes.router import auth

api_router = APIRouter()

api_router.include_router(auth.router)
