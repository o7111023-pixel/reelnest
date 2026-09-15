from datetime import datetime, timedelta, timezone
import secrets

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin


password_hash = PasswordHash.recommended()

ACTIVATION_TOKEN_EXPIRE_HOURS = 24


async def register_user(
    user_data: UserCreate,
    db: AsyncSession,
) -> User:
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("User with this email already exists")

    activation_token = secrets.token_urlsafe(32)
    activation_token_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=ACTIVATION_TOKEN_EXPIRE_HOURS)
    )

    user = User(
        email=user_data.email,
        hashed_password=password_hash.hash(user_data.password),
        activation_token=activation_token,
        activation_token_expires_at=activation_token_expires_at,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    user_data: UserLogin,
    db: AsyncSession,
) -> str:
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("Incorrect email or password")

    if not password_hash.verify(
        user_data.password,
        user.hashed_password,
    ):
        raise ValueError("Incorrect email or password")

    if not user.is_active:
        raise ValueError("User account is not active")

    return create_access_token(user.id)


async def activate_user(
    token: str,
    db: AsyncSession,
) -> User:
    result = await db.execute(
        select(User).where(User.activation_token == token)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("Invalid activation token")

    if user.activation_token_expires_at is None:
        raise ValueError("Activation token has no expiration date")

    if user.activation_token_expires_at < datetime.now(timezone.utc):
        raise ValueError("Activation token has expired")

    user.is_active = True
    user.activation_token = None
    user.activation_token_expires_at = None

    await db.commit()
    await db.refresh(user)

    return user
