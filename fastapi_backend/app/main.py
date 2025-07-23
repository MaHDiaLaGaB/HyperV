from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_users.manager import BaseUserManager
from app.security.auth import get_user_manager
from app.db.database import async_session_maker, engine
from fastapi.middleware.cors import CORSMiddleware
from .helpers.utils import simple_generate_unique_route_id
from app.routes.endpoints import api_router as ap
from app.core.config import settings
from app.core.seeder import seed_superuser
from app.db.init import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start create the db
    await create_db_and_tables()

    # Pre-startup: seed
    async with async_session_maker() as db:# your DI factory
        await seed_superuser(db)
    yield
    # —— SHUTDOWN ——  
    # 1) Gracefully close any pending DB transactions
    await engine.dispose()

app = FastAPI(
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
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
