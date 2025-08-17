from urllib.parse import urlparse
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings

parsed_db_url = urlparse(settings.DATABASE_URL)

async_db_connection_url = (
    f"postgresql+asyncpg://{parsed_db_url.username}:{parsed_db_url.password}@"
    f"{parsed_db_url.hostname}{':' + str(parsed_db_url.port) if parsed_db_url.port else ''}"
    f"{parsed_db_url.path}"
)

# For serverless (Vercel, Fly lite, etc.) keep NullPool. For long-lived servers you can switch to default pool.
engine = create_async_engine(
    async_db_connection_url,
    poolclass=NullPool,
    # echo=True,  # uncomment for SQL debug
)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=settings.EXPIRE_ON_COMMIT,
)
