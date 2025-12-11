"""Database configuration and session management using SQLAlchemy 2.0."""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine database type
db_uri_str = str(settings.SQLALCHEMY_DATABASE_URI).lower()
is_sqlite = "sqlite" in db_uri_str
is_supabase = "supabase.co" in db_uri_str or (
    hasattr(settings, "SUPABASE_DB_URL") and settings.SUPABASE_DB_URL
)

# Connection pool settings
# SQLite doesn't support connection pooling, so use NullPool
# PostgreSQL: Don't specify poolclass - SQLAlchemy will use AsyncAdaptedQueuePool by default
# which is the async-compatible version of QueuePool
pool_kwargs = {}
if is_sqlite:
    pool_kwargs["poolclass"] = NullPool
else:
    # For PostgreSQL (including Supabase), let SQLAlchemy use the default async pool
    # Supabase has connection limits, so we use conservative pool settings
    if is_supabase:
        # Supabase-specific pool settings (more conservative due to connection limits)
        pool_kwargs.update({
            "pool_size": 3,  # Lower pool size for Supabase
            "max_overflow": 5,  # Lower overflow for Supabase
            "pool_pre_ping": True,  # Verify connections before using them
            "pool_recycle": 1800,  # Recycle connections after 30 minutes (shorter for Supabase)
        })
    else:
        # Standard PostgreSQL pool settings
        pool_kwargs.update({
            "pool_size": 5,  # Number of connections to maintain
            "max_overflow": 10,  # Additional connections beyond pool_size
            "pool_pre_ping": True,  # Verify connections before using them
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        })

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

# Ensure SSL is configured for Supabase connections
# Supabase requires SSL connections
# asyncpg uses 'ssl' parameter, but also accepts 'sslmode' for compatibility
if is_supabase and "ssl" not in db_uri.lower() and "sslmode" not in db_uri.lower():
    # Add ssl=require to the connection string if not already present
    separator = "&" if "?" in db_uri else "?"
    db_uri = f"{db_uri}{separator}ssl=require"
    logger.info("Added ssl=require to Supabase connection string")

pool_info = "NullPool" if is_sqlite else "AsyncAdaptedQueuePool (default)"
db_type = "Supabase" if is_supabase else ("SQLite" if is_sqlite else "PostgreSQL")
logger.info(
    f"Database configuration - ENV_STATE: {settings.ENV_STATE}, "
    f"Type: {db_type}, "
    f"URI: {masked_uri}, "
    f"Pool: {pool_info}"
)

# Create async engine with optimized settings
engine = create_async_engine(
    db_uri,
    future=True,  # Use SQLAlchemy 2.0 style
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
