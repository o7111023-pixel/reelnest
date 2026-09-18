from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movie import Movie
from src.models.movie_interaction import Favorite, MovieLike, MovieRating

async def add_favorite(
    user_id: int,
    movie_id: int,
    db: AsyncSession,
) -> Favorite:
    movie_result = await db.execute(
        select(Movie).where(Movie.id == movie_id),
    )
    movie = movie_result.scalar_one_or_none()

    if movie is None:
        raise ValueError("Movie not found")

    favorite_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.movie_id == movie_id,
        ),
    )
    favorite = favorite_result.scalar_one_or_none()

    if favorite is not None:
        raise ValueError("Movie is already in favorites")

    favorite = Favorite(
        user_id=user_id,
        movie_id=movie_id,
    )

    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    return favorite


async def remove_favorite(
    user_id: int,
    movie_id: int,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.movie_id == movie_id,
        ),
    )
    favorite = result.scalar_one_or_none()

    if favorite is None:
        raise ValueError("Movie is not in favorites")

    await db.delete(favorite)
    await db.commit()


async def add_like(
    user_id: int,
    movie_id: int,
    db: AsyncSession,
) -> MovieLike:
    movie_result = await db.execute(
        select(Movie).where(Movie.id == movie_id),
    )
    movie = movie_result.scalar_one_or_none()

    if movie is None:
        raise ValueError("Movie not found")

    like_result = await db.execute(
        select(MovieLike).where(
            MovieLike.user_id == user_id,
            MovieLike.movie_id == movie_id,
        ),
    )
    like = like_result.scalar_one_or_none()

    if like is not None:
        raise ValueError("Movie is already liked")

    like = MovieLike(
        user_id=user_id,
        movie_id=movie_id,
    )

    db.add(like)
    await db.commit()
    await db.refresh(like)

    return like


async def remove_like(
    user_id: int,
    movie_id: int,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(MovieLike).where(
            MovieLike.user_id == user_id,
            MovieLike.movie_id == movie_id,
        ),
    )
    like = result.scalar_one_or_none()

    if like is None:
        raise ValueError("Movie is not liked")

    await db.delete(like)
    await db.commit()


async def add_or_update_rating(
    user_id: int,
    movie_id: int,
    rating,
    db: AsyncSession,
) -> MovieRating:
    movie_result = await db.execute(
        select(Movie).where(Movie.id == movie_id),
    )
    movie = movie_result.scalar_one_or_none()

    if movie is None:
        raise ValueError("Movie not found")

    rating_result = await db.execute(
        select(MovieRating).where(
            MovieRating.user_id == user_id,
            MovieRating.movie_id == movie_id,
        ),
    )
    movie_rating = rating_result.scalar_one_or_none()

    if movie_rating is None:
        movie_rating = MovieRating(
            user_id=user_id,
            movie_id=movie_id,
            rating=rating,
        )
        db.add(movie_rating)
    else:
        movie_rating.rating = rating

    await db.flush()

    average_result = await db.execute(
        select(func.avg(MovieRating.rating)).where(
            MovieRating.movie_id == movie_id,
        ),
    )
    average_rating = average_result.scalar_one()

    movie.rating = round(average_rating, 1)

    await db.commit()
    await db.refresh(movie_rating)

    return movie_rating
