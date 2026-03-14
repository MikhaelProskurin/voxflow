import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine
)
from models.alchemy import Base

postgres_async_engine: AsyncEngine = create_async_engine(url=os.getenv("POSTGRES_DSN"))
async_session_factory = async_sessionmaker[AsyncSession](bind=postgres_async_engine, expire_on_commit=False)

async def create_database_structure() -> None:
    """Create all database tables defined in metadata."""
    async with postgres_async_engine.engine.begin() as conn:
        return await conn.run_sync(Base.metadata.create_all)

async def drop_database_structure() -> None:
    """Drop all database tables defined in metadata."""
    async with postgres_async_engine.engine.begin() as conn:
        return await conn.run_sync(Base.metadata.drop_all)