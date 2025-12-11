import logging
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from fastapi import status, HTTPException, Request, BackgroundTasks
from jose import jwt

from sqlalchemy import select

from app.routers.user import get_user, register, create_access_token, get_password_hash, verify_password, get_current_user, authenticate_user, create_confirmation_token, get_subject_for_token_type
from app.routers import user as user_router
from app.tests.conftest import AsyncSessionTest
from app.models.orm import User as UserORM
from app.models.entities import UserIn
from app.core.config import settings, access_token_expire_minutes, confirm_token_expire_minutes


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
    response = await async_client.post("/register", json=body)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)


@pytest.mark.anyio
async def test_get_user(async_client: AsyncClient, confirmed_user: dict):
    async with AsyncSessionTest() as session:
        user = await get_user(session, email=confirmed_user["email"])
        print(f"confirmed_user: {confirmed_user}")
        assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found(async_client: AsyncClient, confirmed_user: dict):
    async with AsyncSessionTest() as session:
        user = await get_user(session, email="test@example.com")
        assert user is None

@pytest.mark.anyio
async def test_register_user_already_exists(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post("/register", json=confirmed_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already existed" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    # spy = mocker.spy(Request, "url_for")
    spy = mocker.spy(user_router, "send_user_registration_email")

    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    response = await async_client.post("/register", json=body)

    # confirmation_url = str(spy.spy_return)
    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    print(f"confirmation_url: {confirmation_url}")
    response1 = await async_client.get(confirmation_url)

    assert response1.status_code == 200
    assert "User confirmed" == response1.json().get("detail")


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalid-token")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    # Patch token expiry duration so generated token is already expired
    mocker.patch("app.routers.user.confirm_token_expire_minutes", return_value=-1)

    # Spy on *instance method*
    spy = mocker.spy(Request, "url_for")

    body = {
        "id": 123,
        "email": "test@host.com",
        "password": "123456"
    }
    response = await async_client.post("/register", json=body)
    assert response.status_code == 201

    confirmation_url = response.json()["confirmation_url"]  # str(spy.spy_return)
    print(f"confirmation_url: {confirmation_url}")
    response1 = await async_client.get(confirmation_url)
    assert response1.status_code == 401

    # ExpiredSignatureError
    assert "Unauthorized, Token has expired" == response1.json().get("detail")


@pytest.mark.anyio
async def test_register_user_already_exists_direct(async_client: AsyncClient, confirmed_user: dict, request: Request):
    async with AsyncSessionTest() as session:
        background_tasks = BackgroundTasks()
        with pytest.raises(HTTPException) as exc:
            await register(user=UserIn.model_validate(confirmed_user), background_tasks=background_tasks, session=session, request=request)
        assert exc.value.status_code == 400


@pytest.mark.anyio
async def test_password_hashes():
    password = "password"
    assert verify_password(password, get_password_hash(password))


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    form_data = {
        "username": "test@host.com",
        "password": "123456"
    }
    response = await async_client.post("/token", data=form_data)
    assert "Unauthorized" in response.json()["detail"]
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    print(f"confirmed_user: {confirmed_user}")
    form_data = {
        "username": confirmed_user["email"],
        "password": confirmed_user["password"]
    }
    response = await async_client.post("/token", data=form_data)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_login_user_not_confirmed(async_client: AsyncClient, registered_user: dict):
    form_data = {
        "username": registered_user["email"],
        "password": registered_user["password"]
    }
    response = await async_client.post("/token", data=form_data)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_access_token():
    email = "test@email.com"
    token = create_access_token(email=email)
    assert {"sub": email, "type": "access"}.items() <= jwt.decode(
        token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]).items()


@pytest.mark.anyio
async def test_create_confirmation_token():
    email = "test@email.com"
    token = create_confirmation_token(email=email)
    assert {"sub": email, "type": "confirmation"}.items() <= jwt.decode(
        token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]).items()


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_access():
    email = "test@gmail.com"
    token = create_access_token(email=email)
    assert email == get_subject_for_token_type(token=token, payload_type="access")


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_confirmation():
    email = "test@gmail.com"
    token = create_confirmation_token(email=email)
    assert email == get_subject_for_token_type(token=token, payload_type="confirmation")

@pytest.mark.anyio
async def test_get_subject_for_token_type_expired(mocker):
    mocker.patch("app.routers.user.access_token_expire_minutes", return_value=-1)
    email = "test@gmail.com"
    token = create_access_token(email)
    with pytest.raises(HTTPException) as exc:  # ExpiredSignatureError
        get_subject_for_token_type(token, "access")
    assert "Unauthorized, Token has expired" == exc.value.detail


@pytest.mark.anyio
async def test_get_subject_for_token_type_invalid_token():
    token = "invalid-token"
    with pytest.raises(HTTPException) as exc:  # JWTError
        get_subject_for_token_type(token, "access")
    assert f"Unauthorized, invalid token with token: {token}" == exc.value.detail


@pytest.mark.anyio
async def test_get_subject_for_token_type_missing_sub():
    email = "test@gmail.com"
    token = create_access_token(email)
    payload = jwt.decode(
        token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    del payload["sub"]
    token_missing_sub = jwt.encode(
        payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    # simple unittest
    # exp = int(time.time()) + 3600
    # payload = {"exp": exp, "type": "access"}

    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type(token_missing_sub, "access")
    assert "Unauthorized, cannot get sub" == exc.value.detail


@pytest.mark.anyio
async def test_get_subject_for_token_type_wrong_type():
    email = "test@gmail.com"
    token = create_confirmation_token(email)
    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type(token, "access")
    token_type = "confirmation"
    payload_type = "access"
    assert f"Unauthorized, not accept token type={token_type}; payload type={payload_type}" == exc.value.detail


@pytest.mark.anyio
async def test_get_current_user_wrong_type_token(async_client: AsyncClient, confirmed_user: dict):
    # Create token with type="confirmation"
    token = create_confirmation_token(email=confirmed_user["email"])
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            # try to access with 'confirmation' token
            await get_current_user(session=session, token=token)
        assert exc.value.status_code == 401  # Not authentication


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    async with AsyncSessionTest() as session:
        user_result = await authenticate_user(session=session, email=confirmed_user["email"], password=confirmed_user["password"])
        assert user_result.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await authenticate_user(session=session, email="test@home.com", password="123456")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "1-Unauthorized" in exc.value.detail

@pytest.mark.anyio
async def test_authenticate_user_wrong_password(confirmed_user: dict):
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await authenticate_user(session=session, email=confirmed_user["email"], password="wrong password")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "2-Unauthorized" in exc.value.detail

@pytest.mark.anyio
async def test_get_current_user(confirmed_user: dict):
    token = create_access_token(email=confirmed_user["email"])
    async with AsyncSessionTest() as session:
        user = await get_current_user(session=session, token=token)
        assert user.email == confirmed_user["email"]

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    async with AsyncSessionTest() as session:
        with pytest.raises(HTTPException) as exc:
            await get_current_user(session=session, token="invalid-token")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_access_token_expire_minutes():
    assert access_token_expire_minutes() == 30

@pytest.mark.anyio
async def test_confirmation_token_expire_minutes():
    assert confirm_token_expire_minutes() == 60


