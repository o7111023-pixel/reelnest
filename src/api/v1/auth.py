from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.database import get_db
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
)
from src.models.user import User
from src.schemas.user import (
    ActivationResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.services.auth import (
    activate_user,
    authenticate_user,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        user = await register_user(user_data, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticates a user and returns access and refresh JWT tokens.",
)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        access_token, refresh_token = await authenticate_user(
            user_data,
            db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get(
    "/activate/{token}",
    response_model=ActivationResponse,
)
async def activate(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    try:
        await activate_user(token, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ActivationResponse(
        message="User account activated successfully",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Returns a new access and refresh token pair using a valid refresh token.",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user_id = decode_refresh_token(refresh_token)

    result = await db.execute(
        select(User).where(User.id == user_id),
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
