"""Test configuration and fixtures."""
import os
import logging
from typing import AsyncGenerator, Generator

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

os.environ["ENV_STATE"] = "test"

from app.core.config_loader import settings
from app.core.database import get_async_session
from app.main import app
from app.models.orm import Base, Comment, Post, User as UserORM

logger = logging.getLogger(__name__)

# ------------------------------------------
# TEST DATABASE CONFIG
# ------------------------------------------

TEST_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
print(f"TEST_DATABASE_URL: {TEST_DATABASE_URL}")

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    future=True,
    echo=False,
)
AsyncSessionTest = async_sessionmaker(engine_test, expire_on_commit=False)


# ------------------------------------------
# Create schema once per test session
# ------------------------------------------


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    """Create database tables at the start of the test session."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------------------------------------------
# Database cleanup between tests
# ------------------------------------------


@pytest.fixture(autouse=True, scope="function")
async def clean_database():
    """Clean database tables before and after each test to ensure test isolation."""
    # Clean before test
    async with AsyncSessionTest() as session:
        # Delete in reverse order of foreign key dependencies
        await session.execute(delete(Comment))
        await session.execute(delete(Post))
        await session.execute(delete(UserORM))
        await session.commit()

    yield

    # Clean after test
    async with AsyncSessionTest() as session:
        await session.execute(delete(Comment))
        await session.execute(delete(Post))
        await session.execute(delete(UserORM))
        await session.commit()


# ------------------------------------------
# Override FastAPI dependency
# ------------------------------------------


@pytest.fixture
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture(autouse=True)
def apply_overrides(override_get_session):
    """Automatically override get_async_session for all tests."""
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


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    """Create a test user and return its data."""
    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    # Store plain password for tests - register endpoint will hash it
    plain_password = body["password"]
    response = await async_client.post("/register", json=body)
    assert response.status_code == 201
    # Return body with plain password so tests can use it for authentication
    body["password"] = plain_password
    return body

# Authentization
@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
