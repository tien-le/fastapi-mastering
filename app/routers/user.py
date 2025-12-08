import logging
import datetime
from typing import Annotated
from pydantic import ValidationError

from fastapi import HTTPException, APIRouter, Depends, Path, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, ExpiredSignatureError, JWTError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import User as UserORM
from app.models.entities import User, UserIn

from app.core.database import get_async_session
from app.core.config_loader import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

import bcrypt
import hashlib


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")  # /token


def get_password_hash(password: str) -> str:
    """Hash a password using SHA256 and bcrypt."""
    # Pre-hash with SHA256 to remove bcrypt 72-byte limit
    sha = hashlib.sha256(password.encode("utf-8")).digest()
    hashed = bcrypt.hashpw(sha, bcrypt.gensalt())
    return hashed.decode()  # return as str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    sha = hashlib.sha256(plain_password.encode("utf-8")).digest()
    return bcrypt.checkpw(sha, hashed_password.encode())


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    jwt_data = {"sub": email, "exp": expire}
    return jwt.encode(jwt_data, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _convert_user_to_entity(user: UserORM) -> UserIn:
    """Convert ORM User to Pydantic User entity."""
    return UserIn.model_validate(user, from_attributes=True)


async def get_user(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    email: str
) -> UserORM | None:
    """Get User entity based on given email"""
    logger.info("Fetching user entity from DB", extra={"email": email})
    query = select(UserORM).where(UserORM.email == email)
    logger.debug(f"query: {query}")
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def authenticate_user(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    email: str,
    password: str
) -> User | None:
    logger.info("Authenticating User", extra={"email": email})
    user = await get_user(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail=f"1-Unauthorized with given email: {email}; password: xxx",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user_entity = _convert_user_to_entity(user)
    if not verify_password(plain_password=password, hashed_password=user_entity.password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail=f"2-Unauthorized with given email: {email}; password: xxx",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_entity


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserIn | None:
    try:
        payload = jwt.decode(
            token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM])
        # "sub": "email@gmail.com", "exp": 176548579
        # "sub" is the standard claim for subject (usually user identifier)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized, cannot get sub",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized, Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        ) from e
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized with given token",
            headers={"WWW-Authenticate": "Bearer"}
        ) from e
    user = await get_user(session=session, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized, cannot get user information",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return _convert_user_to_entity(user)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User)
async def register(
    user: UserIn,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    existed_user = await get_user(session=session, email=user.email)
    if existed_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"User with email already existed: {user.email}"
        )

    user_detail = user.model_dump()
    user_detail["password"] = get_password_hash(user_detail["password"])

    new_user = UserORM(**user_detail)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.debug(f"Created user with id={new_user.id}")
    return _convert_user_to_entity(new_user)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=list[User]
)
async def get_users(
    session: Annotated[AsyncSession, Depends(get_async_session)]
) -> list[User]:
    """Get all users"""
    logger.info("Fetching all users")
    result = await session.execute(select(UserORM))
    users = result.scalars().all()
    logger.debug(f"Found {len(users)} users.")
    return [_convert_user_to_entity(user) for user in users]


@router.post("/token", response_model=dict)
async def login(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict:
    """Authenticate a user and return an access token.

    Accept either:
    - OAuth2PasswordRequestForm (form-data with username and password)
    - JSON body (UserIn with email and password)
    """
    try:
        # Try to parse as form-data first (OAuth2 standard)
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            username = form_data.get("username")
            form_password = form_data.get("password")
            if username and form_password:
                email = username
                password = form_password
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Missing username or password in form-data"
                )
        else:
            # Try JSON
            try:
                data = await request.json()
                user = UserIn(**data)
                email = user.email
                password = user.password
            except (ValidationError, ValueError, KeyError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON body. Provide email and password fields"
                ) from e

        logger.info("Checking authentication of user", extra={"email": email})
        await authenticate_user(session=session, email=email, password=password)
        access_token = create_access_token(email=email)
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        logger.error(f"Error, due to: {e}", exc_info=True)
        raise
