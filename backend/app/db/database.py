"""
ClaimIQ — Database
SQLAlchemy async engine. Switch SQLite → Postgres by changing DATABASE_URL only.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# connect_args only needed for SQLite
_connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
if "sqlite" in settings.database_url and "file:" in settings.database_url:
    _connect_args["uri"] = True

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
