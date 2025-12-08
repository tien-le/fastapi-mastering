import logging
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from fastapi import status, HTTPException
from jose import jwt

from sqlalchemy import select

from app.routers.user import get_user, register, create_access_token, get_password_hash, verify_password, get_current_user, authenticate_user
from app.tests.conftest import AsyncSessionTest
from app.models.orm import User as UserORM
from app.models.entities import UserIn
from app.core.config_loader import settings


logger = logging.getLogger(__name__)


# User Tests
@pytest.mark.anyio
async def test_create_user(async_client: AsyncClient):
    """Test creating a new post."""
    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    # Send plain password - register endpoint will hash it
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


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    response = await async_client.post("/token", json=body)
    assert "Unauthorized" in response.json()["detail"]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    print(f"registered_user: {registered_user}")
    response = await async_client.post("/token",
        json={
            "id": registered_user["id"],
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_access_token():
    email = "test@email.com"
    token = create_access_token(email=email)
    assert {"sub": email}.items() <= jwt.decode(
        token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]).items()


@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    async with AsyncSessionTest() as session:
        user_result = await authenticate_user(session=session, email=registered_user["email"], password=registered_user["password"])
        assert user_result.email == registered_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await authenticate_user(session=session, email="test@home.com", password="123456")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "1-Unauthorized" in exc.value.detail

@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await authenticate_user(session=session, email=registered_user["email"], password="wrong password")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "2-Unauthorized" in exc.value.detail

@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = create_access_token(email=registered_user["email"])
    async with AsyncSessionTest() as session:
        user = await get_current_user(session=session, token=token)
        assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await get_current_user(session=session, token="invalid-token")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


# Authentization
@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]


