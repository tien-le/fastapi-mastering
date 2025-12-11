"""Database configuration and session management using SQLAlchemy 2.0."""
import logging
import ssl
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

# Ensure SSL is configured for Supabase and cloud PostgreSQL connections
# Supabase and cloud providers (like Render.com) require SSL connections
# asyncpg requires SSL to be configured via connect_args, not as a query parameter
is_cloud_postgres = (
    is_supabase
    or "render.com" in db_uri.lower()
    or "railway.app" in db_uri.lower()
    or "herokuapp.com" in db_uri.lower()
    or "amazonaws.com" in db_uri.lower()
    or "azure.com" in db_uri.lower()
)

# Configure SSL for asyncpg via connect_args
connect_args = {}
if is_cloud_postgres and not is_sqlite:
    # Remove any ssl/sslmode query parameters from the URI (asyncpg doesn't use them)
    parsed = urlparse(db_uri)
    query_params = parse_qs(parsed.query)

    # Check if SSL mode is specified in query params
    ssl_mode = None
    if "sslmode" in query_params:
        ssl_mode = query_params["sslmode"][0].lower()
    elif "ssl" in query_params:
        ssl_mode = query_params["ssl"][0].lower()

    # Remove ssl/sslmode parameters from URI (asyncpg doesn't use query params for SSL)
    query_params.pop("ssl", None)
    query_params.pop("sslmode", None)

    # Reconstruct URI without ssl parameters
    if query_params:
        new_query = urlencode(query_params, doseq=True)
        db_uri = urlunparse(parsed._replace(query=new_query))
    else:
        db_uri = urlunparse(parsed._replace(query=""))

    # Configure SSL for asyncpg based on ssl_mode or default to require
    if ssl_mode == "disable":
        # Don't configure SSL
        logger.info("SSL disabled per connection string")
    elif ssl_mode in ("require", "prefer", None):
        # Use SSL with certificate verification (default for cloud databases)
        # For most cloud providers, we want to verify certificates
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context
        logger.info(f"Configured SSL with certificate verification for {'Supabase' if is_supabase else 'cloud PostgreSQL'}")
    elif ssl_mode in ("allow", "verify-ca", "verify-full"):
        # verify-ca or verify-full: use default context (verifies certificates)
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context
        logger.info(f"Configured SSL with certificate verification (mode: {ssl_mode})")
    else:
        # Default: require SSL with verification
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context
        logger.info(f"Configured SSL (default) for {'Supabase' if is_supabase else 'cloud PostgreSQL'}")

pool_info = "NullPool" if is_sqlite else "AsyncAdaptedQueuePool (default)"
db_type = "Supabase" if is_supabase else ("SQLite" if is_sqlite else "PostgreSQL")
is_cloud = is_cloud_postgres or "render.com" in db_uri.lower() or "railway.app" in db_uri.lower()
logger.info(
    f"Database configuration - ENV_STATE: {settings.ENV_STATE}, "
    f"Type: {db_type}, "
    f"Cloud: {is_cloud}, "
    f"URI: {masked_uri}, "
    f"Pool: {pool_info}"
)

# Create async engine with optimized settings
engine = create_async_engine(
    db_uri,
    future=True,  # Use SQLAlchemy 2.0 style
    connect_args=connect_args if connect_args else {},
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
