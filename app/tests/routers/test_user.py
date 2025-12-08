import logging
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from fastapi import status, HTTPException

from sqlalchemy import select

from app.routers.user import get_user, register
from app.tests.conftest import AsyncSessionTest
from app.models.orm import User as UserORM
from app.models.entities import UserIn
from app.routers.user import get_password_hash, verify_password

logger = logging.getLogger(__name__)


# Fixtures
# @pytest.fixture()
# async def registered_user(async_client: AsyncClient) -> dict:
#     user_details = {"email": "test@host.com", "password": "123456"}
#     await async_client.post("/register", json=user_details)

#     async with AsyncSessionTest() as session:
#         query = select(UserORM).where(UserORM.email==user_details["email"])
#         result = await session.execute(query)
#         user = result.scalar_one_or_none()
#         if user:
#             user_details["id"] = user.id
#         else:
#             logger.debug(f"User Not Found with email: {user_details["email"]}")
#     return user_details

@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    """Create a test user and return its data."""
    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    body["password"] = get_password_hash(body["password"])
    response = await async_client.post("/register", json=body)
    assert response.status_code == 201
    return body


# User Tests
@pytest.mark.anyio
async def test_create_user(async_client: AsyncClient):
    """Test creating a new post."""
    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    body["password"] = get_password_hash(body["password"])
    response = await async_client.post("/register", json=body)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)


@pytest.mark.anyio
async def test_get_user(async_client: AsyncClient, registered_user: dict):
    async with AsyncSessionTest() as session:
        user = await get_user(session, email=registered_user["email"])
        print(f"registered_user: {registered_user}")
        assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found(async_client: AsyncClient, registered_user: dict):
    async with AsyncSessionTest() as session:
        user = await get_user(session, email="test@example.com")
        assert user is None

@pytest.mark.anyio
async def test_register_user_already_exists(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post("/register", json=registered_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already existed" in response.json()["detail"]

@pytest.mark.anyio
async def test_register_user_already_exists_direct(async_client: AsyncClient, registered_user: dict):
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await register(user=UserIn.model_validate(registered_user), session=session)
        assert exc.value.status_code == 400

@pytest.mark.anyio
async def test_password_hashes():
    password = "password"
    assert verify_password(password, get_password_hash(password))
