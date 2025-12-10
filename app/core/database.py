"""Database configuration and session management using SQLAlchemy 2.0."""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config_loader import settings

logger = logging.getLogger(__name__)

# Create async engine with optimized settings
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    future=True,  # Use SQLAlchemy 2.0 style
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent expired instances after commit
    autoflush=False,  # Manual flush control
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Yields:
        AsyncSession: Database session

    The session is automatically committed on success or rolled back on exception.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
            logger.debug("Database session committed successfully")
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rolled back due to error: {e}", exc_info=True)
            raise
        finally:
            await session.close()
