from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
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
)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        access_token = await authenticate_user(user_data, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=access_token,
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
