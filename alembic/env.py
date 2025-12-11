import logging
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.models.orm import Post, Comment, User, Like
from app.core.config import settings

# Set up logging before fileConfig
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Log environment info for debugging
logger.info(f"Alembic - ENV_STATE: {settings.ENV_STATE}")
logger.info(f"Alembic - DATABASE_URL from env: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
logger.info(f"Alembic - PROD_DATABASE_URL from env: {'SET' if os.getenv('PROD_DATABASE_URL') else 'NOT SET'}")
logger.info(f"Alembic - DEV_DATABASE_URL from env: {'SET' if os.getenv('DEV_DATABASE_URL') else 'NOT SET'}")

# Convert async database URL to sync for Alembic
# Alembic requires synchronous connections
database_url = str(settings.SQLALCHEMY_DATABASE_URI)

# On cloud platforms like Render, DATABASE_URL is often provided directly
# Check if DATABASE_URL exists in environment and use it if:
# 1. We're in production, OR
# 2. The settings returned SQLite/localhost (fallback)
env_db_url = os.getenv("DATABASE_URL")
if env_db_url:
    if settings.ENV_STATE == "prod":
        # In production, always prefer DATABASE_URL from environment
        logger.info("Alembic - Production environment detected, using DATABASE_URL from environment")
        database_url = env_db_url
    elif "sqlite" in database_url.lower() or "localhost" in database_url.lower():
        # If settings fell back to SQLite/localhost, use environment variable
        logger.warning(
            f"Alembic - Settings returned {database_url}, but found DATABASE_URL in environment. "
            "Using environment variable directly."
        )
        database_url = env_db_url
elif ("sqlite" in database_url.lower() or "localhost" in database_url.lower()) and settings.ENV_STATE == "prod":
    # In production, we must have a valid database URL
    logger.error(
        f"Alembic - No valid database URL found in production. Settings returned: {database_url}. "
        "Please set DATABASE_URL environment variable."
    )
    raise ValueError(
        "No database URL configured for production. Please set DATABASE_URL environment variable."
    )

logger.info(f"Alembic - Original database URL: {database_url.split('@')[0] if '@' in database_url else database_url.split('://')[0]}@***")

# Replace async drivers with sync ones for Alembic
# Alembic requires synchronous database connections
if "sqlite+aiosqlite://" in database_url:
    database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
elif "postgresql+asyncpg://" in database_url:
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://") and "+" not in database_url:
    # If it's already postgresql:// without a driver, add psycopg2
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Log the converted URL (masked)
masked_url = database_url.split("@")[0] + "@***" if "@" in database_url else database_url.split("://")[0] + "://***"
logger.info(f"Alembic - Converted database URL: {masked_url}")

# Set the DB URL
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.models.orm import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
