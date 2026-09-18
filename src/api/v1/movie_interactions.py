from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.schemas.movie_interaction import (
    InteractionResponse,
    MovieRatingCreate,
    MovieRatingResponse,
)
from src.services.movie_interaction import (
    add_favorite,
    add_like,
    add_or_update_rating,
    remove_favorite,
    remove_like,
)


router = APIRouter(
    prefix="/movies",
    tags=["Movie Interactions"],
)


@router.post(
    "/{movie_id}/favorite",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to favorites",
)
async def add_movie_to_favorites(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    try:
        await add_favorite(
            user_id=current_user.id,
            movie_id=movie_id,
            db=db,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Movie not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc

    return InteractionResponse(
        message="Movie added to favorites",
    )


@router.delete(
    "/{movie_id}/favorite",
    response_model=InteractionResponse,
    summary="Remove movie from favorites",
)
async def remove_movie_from_favorites(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    try:
        await remove_favorite(
            user_id=current_user.id,
            movie_id=movie_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InteractionResponse(
        message="Movie removed from favorites",
    )


@router.post(
    "/{movie_id}/like",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Like a movie",
)
async def like_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    try:
        await add_like(
            user_id=current_user.id,
            movie_id=movie_id,
            db=db,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Movie not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc

    return InteractionResponse(
        message="Movie liked",
    )


@router.delete(
    "/{movie_id}/like",
    response_model=InteractionResponse,
    summary="Unlike a movie",
)
async def unlike_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    try:
        await remove_like(
            user_id=current_user.id,
            movie_id=movie_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InteractionResponse(
        message="Movie unliked",
    )


@router.post(
    "/{movie_id}/rating",
    response_model=MovieRatingResponse,
    status_code=status.HTTP_200_OK,
    summary="Rate a movie",
    description="Creates or updates the current user's rating for a movie.",
)
async def rate_movie(
    movie_id: int,
    rating_data: MovieRatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieRatingResponse:
    try:
        movie_rating = await add_or_update_rating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=rating_data.rating,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return MovieRatingResponse(
        rating=movie_rating.rating,
        movie_rating=movie_rating.rating,
    )
