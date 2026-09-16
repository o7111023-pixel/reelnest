import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.schemas.movie import (
    MovieCreate,
    MovieListResponse,
    MovieResponse,
    MovieUpdate,
)
from src.services.movie import (
    create_movie,
    delete_movie,
    get_movie_by_id,
    list_movies,
    update_movie,
)


router = APIRouter(
    prefix="/movies",
    tags=["Movies"],
)


@router.get(
    "",
    response_model=MovieListResponse,
    summary="Get movie catalog",
    description=(
        "Returns a paginated movie catalog with "
        "search, filtering and sorting."
    ),
)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    genre_id: int | None = Query(None, ge=1),
    release_year: int | None = Query(
        None,
        ge=1888,
        le=2100,
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(title|release_year|rating|price|created_at)$",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponse:
    movies, total = await list_movies(
        db=db,
        page=page,
        per_page=per_page,
        search=search,
        genre_id=genre_id,
        release_year=release_year,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = math.ceil(total / per_page) if total else 0

    return MovieListResponse(
        items=movies,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Get movie by ID",
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieResponse:
    movie = await get_movie_by_id(movie_id, db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return movie


@router.post(
    "",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create movie",
    description=(
        "Creates a new movie. "
        "Authentication is required."
    ),
)
async def create_movie_endpoint(
    movie_data: MovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MovieResponse:
    try:
        movie = await create_movie(movie_data, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return movie


@router.patch(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Update movie",
    description=(
        "Updates an existing movie. "
        "Authentication is required."
    ),
)
async def update_movie_endpoint(
    movie_id: int,
    movie_data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MovieResponse:
    movie = await get_movie_by_id(movie_id, db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    try:
        movie = await update_movie(
            movie,
            movie_data,
            db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movie",
    description=(
        "Deletes a movie. "
        "Authentication is required."
    ),
)
async def delete_movie_endpoint(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    movie = await get_movie_by_id(movie_id, db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    await delete_movie(movie, db)
