"""Application configuration using Pydantic Settings."""
import logging
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from string or list.

    Args:
        v: CORS origins as string (comma-separated) or list

    Returns:
        Parsed CORS origins as list or string

    Raises:
        ValueError: If input format is invalid
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(f"Invalid CORS format: {v}")


def access_token_expire_minutes() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30

def confirm_token_expire_minutes() -> int:
    return settings.CONFIRM_TOKEN_EXPIRE_MINUTES or 60


# ---------------------------------------------------------
# Base
# ---------------------------------------------------------
class BaseConfig(BaseSettings):
    ENV_STATE: Literal["dev", "prod", "test"] = "dev"

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

    Attributes:
        DOMAIN: Server domain name
        JWT_SECRET_KEY: Secret key for JWT tokens
        JWT_ALGORITHM: Algorithm for JWT signing
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
        BACKEND_CORS_ORIGINS: Allowed CORS origins
        POSTGRESQL_*: PostgreSQL connection parameters
        DB_FORCE_ROLLBACK: Force rollback after each request (testing)
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

    POSTGRESQL_USERNAME: str | None = Field(default=None, description="PostgreSQL username")
    POSTGRESQL_PASSWORD: str | None = Field(default=None, description="PostgreSQL password")
    POSTGRESQL_SERVER: str | None = Field(default=None, description="PostgreSQL server host")
    POSTGRESQL_PORT: int | None = Field(default=None, ge=1, le=65535, description="PostgreSQL port")
    POSTGRESQL_DATABASE: str | None = Field(default=None, description="PostgreSQL database name")

    DB_FORCE_ROLLBACK: bool = Field(
        default=False, description="Force rollback after each request (for testing)"
    )

    LOGTAIL_API_KEY: str | None = None

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

        Returns:
            Database URI string (SQLite if PostgreSQL not configured, else PostgreSQL)
        """
        if not all(
            [
                self.POSTGRESQL_USERNAME,
                self.POSTGRESQL_PASSWORD,
                self.POSTGRESQL_SERVER,
                self.POSTGRESQL_PORT,
                self.POSTGRESQL_DATABASE,
            ]
        ):
            logger.debug("Using sqlite in local.db")
            return "sqlite+aiosqlite:///./local.db"

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
    model_config = SettingsConfigDict(env_prefix="DEV_", extra="ignore")
    DB_FORCE_ROLLBACK: bool = False


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_", extra="ignore")


class TestConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="TEST_", extra="ignore")
    DB_FORCE_ROLLBACK: bool = True

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
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
