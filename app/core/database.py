"""Database configuration and session management using SQLAlchemy 2.0."""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine if we're using SQLite (for connection pool settings)
is_sqlite = "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI).lower()

# Connection pool settings
# SQLite doesn't support connection pooling, so use NullPool
# PostgreSQL should use QueuePool for better performance
pool_class = NullPool if is_sqlite else QueuePool
pool_kwargs = {} if is_sqlite else {
    "pool_size": 5,  # Number of connections to maintain
    "max_overflow": 10,  # Additional connections beyond pool_size
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_recycle": 3600,  # Recycle connections after 1 hour
}

# Log database URI (masked for security)
db_uri = str(settings.SQLALCHEMY_DATABASE_URI)
if "@" in db_uri:
    # Mask credentials in the URI
    parts = db_uri.split("@")
    if len(parts) == 2:
        scheme_part = parts[0].split("://")
        if len(scheme_part) == 2:
            masked_uri = f"{scheme_part[0]}://***:***@{parts[1]}"
        else:
            masked_uri = f"***@{parts[1]}"
    else:
        masked_uri = "***@***"
else:
    masked_uri = db_uri.split("://")[0] + "://***" if "://" in db_uri else "***"

logger.info(
    f"Database configuration - ENV_STATE: {settings.ENV_STATE}, "
    f"URI: {masked_uri}, "
    f"Pool: {pool_class.__name__}, "
    f"SQLite: {is_sqlite}"
)

# Create async engine with optimized settings
engine = create_async_engine(
    db_uri,
    future=True,  # Use SQLAlchemy 2.0 style
    poolclass=pool_class,
    **pool_kwargs,
    echo=False,  # Set to True for SQL query logging
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
