from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .helpers.utils import simple_generate_unique_route_id
from app.routes.endpoints import api_router as ap
from app.core.config import settings

app = FastAPI(
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
)

# Middleware for CORS configuration
CORS_ORIGINS = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include items routes
app.include_router(ap)
