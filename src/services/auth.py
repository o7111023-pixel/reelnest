from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin


password_hash = PasswordHash.recommended()


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

    user = User(
        email=user_data.email,
        hashed_password=password_hash.hash(user_data.password),
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
