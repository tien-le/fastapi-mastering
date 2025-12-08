import logging
from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends, Path, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import User as UserORM
from app.models.entities import User, UserIn

from app.core.database import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

import bcrypt
import hashlib

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



def _convert_user_to_entity(user: UserORM) -> User:
    """Convert ORM User to Pydantic User entity."""
    return User.model_validate(user, from_attributes=True)


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
