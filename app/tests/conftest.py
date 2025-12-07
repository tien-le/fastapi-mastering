import os
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

os.environ["ENV_STATE"] = "test"

from app.main import app
from app.core.database import get_async_session
from app.models.orm import Base
from app.core.config_loader import settings

# ------------------------------------------
# TEST DATABASE CONFIG
# ------------------------------------------

# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # Or use a test Postgres DB
TEST_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
print(f"TEST_DATABASE_URL: {TEST_DATABASE_URL}")

engine_test = create_async_engine(TEST_DATABASE_URL, future=True)
AsyncSessionTest = async_sessionmaker(engine_test, expire_on_commit=False)


# ------------------------------------------
# Create schema once per test session
# ------------------------------------------


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------------------------------------------
# Override FastAPI dependency
# ------------------------------------------


@pytest.fixture
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture(autouse=True)
def apply_overrides(override_get_session):
    """
    Automatically override get_async_session for all tests.
    """
    app.dependency_overrides[get_async_session] = lambda: override_get_session
    yield
    app.dependency_overrides.clear()


# ------------------------------------------
# Sync TestClient (for non-async tests)
# ------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


# ------------------------------------------
# Async Test Client
# ------------------------------------------


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=client.base_url) as ac:
        yield ac
