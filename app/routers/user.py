import logging
import datetime
import bcrypt
import hashlib
from typing import Annotated, Literal

from fastapi import HTTPException, APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, ExpiredSignatureError, JWTError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import User as UserORM
from app.models.entities import User, UserIn, UserRegistrationResponse

from app.core.database import get_async_session
from app.core.config_loader import settings, access_token_expire_minutes, confirm_token_expire_minutes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


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
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    return jwt.encode(jwt_data, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    return jwt.encode(
        jwt_data,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM)


def get_exception_401(detail: str) -> HTTPException:
    """Return HTTPException"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_exception_400(detail: str) -> HTTPException:
    """Return HTTPException"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_subject_for_token_type(token: str, payload_type: Literal["access", "confirmation"]) -> str:
    try:
        payload = jwt.decode(
            token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as e:
        detail = "Unauthorized, Token has expired"
        raise get_exception_401(detail) from e
    except JWTError as e:
        detail = f"Unauthorized, invalid token with token: {token}"
        raise get_exception_401(detail) from e

    # "sub": "email@gmail.com", "exp": 176548579
    # "sub" is the standard claim for subject (usually user identifier)
    email = payload.get("sub")
    if email is None:
        detail = "Unauthorized, cannot get sub"
        raise get_exception_401(detail)

    token_type = payload.get("type")
    if token_type is None or (token_type != payload_type):
        detail = f"Unauthorized, not accept token type={token_type}; payload type={payload_type}"
        raise get_exception_401(detail)
    return email


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
        raise get_exception_401(f"1-Unauthorized with given email: {email}; password: xxx")
    user_entity = _convert_user_to_entity(user)
    if not verify_password(plain_password=password, hashed_password=user_entity.password):
        raise get_exception_401(f"2-Unauthorized with given email: {email}; password: xxx")
    if not user.confirmed:
        raise get_exception_401(f"Unauthorized, User has not confirmed email.")
    return user_entity


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserIn | None:
    headers = {"WWW-Authenticate": "Bearer"}
    email = get_subject_for_token_type(token=token, payload_type="access")
    user = await get_user(session=session, email=email)
    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized, cannot get user information",
            headers=headers
        )
    return _convert_user_to_entity(user)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegistrationResponse)
async def register(
    user: UserIn,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    request: Request
) -> UserRegistrationResponse:
    existed_user = await get_user(session=session, email=user.email)
    if existed_user:
        raise get_exception_400(detail = f"User with email already existed: {user.email}")
    user_detail = user.model_dump()
    user_detail["password"] = get_password_hash(user_detail["password"])

    new_user = UserORM(**user_detail)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.debug(f"Created user with id={new_user.id}")
    return UserRegistrationResponse(
        id=new_user.id,
        email=new_user.email,
        detail="User created. Please confirm your email.",
        confirmation_url=str(request.url_for(
            "confirm_email", token=create_confirmation_token(new_user.email)
        ))
    )


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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict:
    """Authenticate a user and return an access token.

    Uses OAuth2PasswordRequestForm (form-data with username and password).
    The username field should contain the user's email address.
    """
    email = form_data.username
    password = form_data.password

    logger.info("Checking authentication of user", extra={"email": email})
    await authenticate_user(session=session, email=email, password=password)
    access_token = create_access_token(email=email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token: str
) -> dict:
    email = get_subject_for_token_type(token, "confirmation")

    # Method 1: select & update
    query = select(UserORM).where(UserORM.email==email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found with email: {email}")
    user.confirmed = True
    await session.commit()

    # Method 2: update
    # Update column 'confirmed' = True
    # query = (
    #     update(UserORM)
    #     .where(UserORM.email == email)
    #     .values(confirmed=True)
    #     .execution_options(synchronize_session="fetch")
    # )
    # logger.debug(f"query: {query}")
    # await session.execute(query)
    # await session.commit()

    return {"detail": "User confirmed"}


