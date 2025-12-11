"""Application configuration using Pydantic Settings."""
import logging
import os
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from string or list.

    Converts comma-separated string of origins into a list, or returns
    the value as-is if it's already a list or JSON array string.

    Args:
        v: CORS origins as string (comma-separated) or list

    Returns:
        Parsed CORS origins as list or string (if JSON array format)

    Raises:
        ValueError: If input format is invalid
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(f"Invalid CORS format: {v}")


def access_token_expire_minutes() -> int:
    """Get access token expiration time in minutes.

    Returns:
        Access token expiration time in minutes (default: 30)
    """
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30


def confirm_token_expire_minutes() -> int:
    """Get confirmation token expiration time in minutes.

    Returns:
        Confirmation token expiration time in minutes (default: 60)
    """
    return settings.CONFIRM_TOKEN_EXPIRE_MINUTES or 60


# ---------------------------------------------------------
# Base
# ---------------------------------------------------------
class BaseConfig(BaseSettings):
    """Base configuration class with common settings.

    Provides the foundation for environment-specific configurations.
    All configuration classes inherit from this base class.

    Attributes:
        ENV_STATE: Current environment state (dev, prod, or test)
    """

    ENV_STATE: Literal["dev", "prod", "test"] = Field(
        default="dev", description="Current environment state"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )


# ---------------------------------------------------------
# Global Shared Config
# ---------------------------------------------------------
class GlobalConfig(BaseConfig):
    """Global configuration shared across all environments.

    This class contains all configuration settings that are shared across
    different environment configurations (dev, prod, test). Environment-specific
    configs inherit from this class and can override values as needed.

    Attributes:
        DOMAIN: Server domain name
        JWT_SECRET_KEY: Secret key for JWT tokens
        JWT_ALGORITHM: Algorithm for JWT signing
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiration time in minutes
        CONFIRM_TOKEN_EXPIRE_MINUTES: Confirmation token expiration time in minutes
        MAILGUN_API_KEY: Mailgun API key for email service
        MAILGUN_DOMAIN: Mailgun domain for email service
        B2_KEY_ID: Backblaze B2 key ID for object storage
        B2_APPLICATION_KEY: Backblaze B2 application key for object storage
        B2_BUCKET_NAME: Backblaze B2 bucket name for object storage
        BACKEND_CORS_ORIGINS: Allowed CORS origins
        POSTGRESQL_*: PostgreSQL connection parameters (username, password, server, port, database)
        DB_FORCE_ROLLBACK: Force rollback after each request (for testing)
        LOGTAIL_API_KEY: Logtail API key for log aggregation
    """

    DOMAIN: str = Field(default="localhost", description="Server domain name")

    JWT_SECRET_KEY: str = Field(default="dev-key", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, ge=1, description="Token expiration time in minutes"
    )
    CONFIRM_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, ge=1, description="Confirm Token expiration time in minutes"
    )

    # MailGun
    MAILGUN_API_KEY: str | None = None
    MAILGUN_DOMAIN: str | None = None

    # Backblaze B2
    B2_KEY_ID: str | None = None
    B2_APPLICATION_KEY: str | None = None
    B2_BUCKET_NAME: str | None = None

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str,
        BeforeValidator(parse_cors),
    ] = Field(default_factory=list, description="Allowed CORS origins")

    # Support DATABASE_URL for cloud platforms (e.g., Render.com)
    DATABASE_URL: str | None = Field(default=None, description="Full database connection URL")

    POSTGRESQL_USERNAME: str | None = Field(default=None, description="PostgreSQL username")
    POSTGRESQL_PASSWORD: str | None = Field(default=None, description="PostgreSQL password")
    POSTGRESQL_SERVER: str | None = Field(default=None, description="PostgreSQL server host")
    POSTGRESQL_PORT: int | None = Field(default=None, ge=1, le=65535, description="PostgreSQL port")
    POSTGRESQL_DATABASE: str | None = Field(default=None, description="PostgreSQL database name")

    DB_FORCE_ROLLBACK: bool = Field(
        default=False, description="Force rollback after each request (for testing)"
    )

    LOGTAIL_API_KEY: str | None = Field(
        default=None, description="Logtail API key for log aggregation"
    )

    @computed_field
    @property
    def server_host(self) -> str:
        """Compute server host URL based on environment.

        Returns:
            Server URL (http for local, https otherwise)
        """
        # Use HTTPS for anything other than local development
        if self.ENV_STATE == "dev":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    def build_db_uri(self) -> str:
        """Build database URI from configuration.

        Priority:
        1. DATABASE_URL from model (with env prefix if applicable)
        2. Unprefixed DATABASE_URL from environment (for cloud platforms like Render.com)
        3. Individual PostgreSQL components
        4. SQLite fallback for local development

        Returns:
            Database URI string (SQLite if PostgreSQL not configured, else PostgreSQL)
        """
        # Check for DATABASE_URL from model first (respects env prefix)
        db_url = self.DATABASE_URL

        # Also check unprefixed DATABASE_URL directly from environment
        # This handles cases where cloud platforms provide DATABASE_URL without prefix
        if not db_url:
            db_url = os.getenv("DATABASE_URL")

        if db_url:
            db_url = str(db_url)
            # Convert postgresql:// to postgresql+asyncpg:// if needed
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            # If already asyncpg, use as-is
            if "postgresql+asyncpg://" in db_url or "sqlite+aiosqlite://" in db_url:
                logger.debug(f"Using DATABASE_URL: {db_url.split('@')[0] if '@' in db_url else db_url.split('://')[0]}@***")
                return db_url
            logger.debug(f"Using DATABASE_URL (converted to asyncpg): {db_url.split('@')[0] if '@' in db_url else db_url.split('://')[0]}@***")
            return db_url

        # Fall back to individual components
        if all(
            [
                self.POSTGRESQL_USERNAME,
                self.POSTGRESQL_PASSWORD,
                self.POSTGRESQL_SERVER,
                self.POSTGRESQL_PORT,
                self.POSTGRESQL_DATABASE,
            ]
        ):
            return str(
                MultiHostUrl.build(
                    scheme="postgresql+asyncpg",
                    username=self.POSTGRESQL_USERNAME,
                    password=self.POSTGRESQL_PASSWORD,
                    host=self.POSTGRESQL_SERVER,
                    port=self.POSTGRESQL_PORT,
                    path=self.POSTGRESQL_DATABASE,
                )
            )

        # SQLite fallback when PostgreSQL is not configured
        # Use ENV_STATE-based filename (e.g., dev.db, prod.db, test.db)
        sqlite_filename = f"{self.ENV_STATE}.db"
        logger.debug(f"Using sqlite in {sqlite_filename}")
        return f"sqlite+aiosqlite:///./{sqlite_filename}"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get SQLAlchemy database URI.

        Returns:
            Database URI string
        """
        return self.build_db_uri()


# ---------------------------------------------------------
# Environment-Specific
# ---------------------------------------------------------
class DevConfig(GlobalConfig):
    """Development environment configuration.

    Uses DEV_ prefix for environment variables. Defaults to no forced rollback.
    """

    model_config = SettingsConfigDict(env_prefix="DEV_", extra="ignore")
    DB_FORCE_ROLLBACK: bool = False


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_", extra="ignore")


class TestConfig(GlobalConfig):
    """Test environment configuration.

    Uses TEST_ prefix for environment variables. Forces rollback after each
    request and uses a separate test database (test.db).
    """

    model_config = SettingsConfigDict(env_prefix="TEST_", extra="ignore")
    DB_FORCE_ROLLBACK: bool = True

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get SQLAlchemy database URI for testing.

        Returns:
            SQLite database URI pointing to test.db
        """
        logger.debug("Using sqlite in test.db")
        return "sqlite+aiosqlite:///./test.db"


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------
@lru_cache()
def get_settings() -> GlobalConfig:
    """Get application settings based on ENV_STATE.

    Returns:
        Configuration instance for the current environment

    The function is cached to avoid reloading settings on every call.
    """
    base = BaseConfig()

    mapping: dict[str, type[GlobalConfig]] = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }

    config_class = mapping.get(base.ENV_STATE, DevConfig)
    return config_class()  # Loads ENV-specific values from .env


settings = get_settings()
