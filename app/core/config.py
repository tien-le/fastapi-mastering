from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


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
    DOMAIN: str = "localhost"

    JWT_SECRET_KEY: str = "dev-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str,
        BeforeValidator(parse_cors),
    ] = Field(default_factory=list)

    @computed_field
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    POSTGRESQL_USERNAME: str | None = None
    POSTGRESQL_PASSWORD: str | None = None
    POSTGRESQL_SERVER: str | None = None
    POSTGRESQL_PORT: int | None = None
    POSTGRESQL_DATABASE: str | None = None

    DB_FORCE_ROLLBACK: bool = False

    # Build database URI
    def build_db_uri(self) -> str:
        if not all(
            [
                self.POSTGRESQL_USERNAME,
                self.POSTGRESQL_PASSWORD,
                self.POSTGRESQL_SERVER,
                self.POSTGRESQL_PORT,
                self.POSTGRESQL_DATABASE,
            ]
        ):
            return "sqlite+aiosqlite:///./local.db"

        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",  # psycopg2
            username=self.POSTGRESQL_USERNAME,
            password=self.POSTGRESQL_PASSWORD,
            host=self.POSTGRESQL_SERVER,
            port=self.POSTGRESQL_PORT,
            path=self.POSTGRESQL_DATABASE,
        )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.build_db_uri()


# ---------------------------------------------------------
# Environment-Specific
# ---------------------------------------------------------
class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")
    DB_FORCE_ROLLBACK: bool = False


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


class TestConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="TEST_")
    DB_FORCE_ROLLBACK: bool = True

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return "sqlite+aiosqlite:///./test.db"


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------
@lru_cache()
def get_settings() -> GlobalConfig:
    base = BaseConfig()

    mapping = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }

    if base.ENV_STATE in mapping:
        return mapping[base.ENV_STATE]()  # loads ENV-specific values from .env
    return DevConfig()


settings = get_settings()
