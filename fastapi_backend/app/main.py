# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.seeder import seed_core
from app.db.database import async_session_maker, engine
from app.db.init import ensure_extensions, create_db_and_tables  # keep create_all for dev only
from app.routes.endpoints import api_router as ap
from app.helpers.utils import simple_generate_unique_route_id  # adjust import path if needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- STARTUP ----
    # Ensure pgcrypto for server_default gen_random_uuid()
    await ensure_extensions()

    # Dev convenience: create tables if not using Alembic locally.
    # In production, rely on Alembic migrations and remove this line.
    await create_db_and_tables()

    # Seed core data (system org + superadmin role + optional local rows for SUPERADMINS)
    async with async_session_maker() as db:
        await seed_core(db)

    yield

    # ---- SHUTDOWN ----
    await engine.dispose()


app = FastAPI(
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL if hasattr(settings, "OPENAPI_URL") else "/openapi.json",
    lifespan=lifespan,
)

# CORS
cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ap)
