from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.actor import Actor
from src.models.director import Director
from src.models.genre import Genre
from src.models.movie import Movie


async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession,
) -> Movie | None:
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.director),
            selectinload(Movie.genres),
            selectinload(Movie.actors),
        )
        .where(Movie.id == movie_id),
    )
    return result.scalar_one_or_none()


async def create_movie(movie_data, db: AsyncSession) -> Movie:
    director = None

    if movie_data.director_id is not None:
        result = await db.execute(
            select(Director).where(
                Director.id == movie_data.director_id,
            ),
        )
        director = result.scalar_one_or_none()

        if director is None:
            raise ValueError("Director not found")

    genres = []
    if movie_data.genre_ids:
        result = await db.execute(
            select(Genre).where(
                Genre.id.in_(movie_data.genre_ids),
            ),
        )
        genres = list(result.scalars().all())

    actors = []
    if movie_data.actor_ids:
        result = await db.execute(
            select(Actor).where(
                Actor.id.in_(movie_data.actor_ids),
            ),
        )
        actors = list(result.scalars().all())

    movie = Movie(
        title=movie_data.title,
        description=movie_data.description,
        release_year=movie_data.release_year,
        duration_minutes=movie_data.duration_minutes,
        poster_url=(
            str(movie_data.poster_url)
            if movie_data.poster_url
            else None
        ),
        rating=movie_data.rating,
        price=movie_data.price,
        director_id=movie_data.director_id,
        director=director,
        genres=genres,
        actors=actors,
    )

    db.add(movie)
    await db.commit()

    return await get_movie_by_id(movie.id, db)


async def update_movie(
    movie: Movie,
    movie_data,
    db: AsyncSession,
) -> Movie:
    update_data = movie_data.model_dump(
        exclude_unset=True,
        exclude={"genre_ids", "actor_ids"},
    )

    if "poster_url" in update_data and update_data["poster_url"]:
        update_data["poster_url"] = str(update_data["poster_url"])

    if movie_data.director_id is not None:
        result = await db.execute(
            select(Director).where(
                Director.id == movie_data.director_id,
            ),
        )
        director = result.scalar_one_or_none()

        if director is None:
            raise ValueError("Director not found")

    for field, value in update_data.items():
        setattr(movie, field, value)

    if movie_data.genre_ids is not None:
        result = await db.execute(
            select(Genre).where(
                Genre.id.in_(movie_data.genre_ids),
            ),
        )
        movie.genres = list(result.scalars().all())

    if movie_data.actor_ids is not None:
        result = await db.execute(
            select(Actor).where(
                Actor.id.in_(movie_data.actor_ids),
            ),
        )
        movie.actors = list(result.scalars().all())

    await db.commit()

    return await get_movie_by_id(movie.id, db)


async def delete_movie(
    movie: Movie,
    db: AsyncSession,
) -> None:
    await db.delete(movie)
    await db.commit()


async def list_movies(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    search: str | None = None,
    genre_id: int | None = None,
    release_year: int | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Movie], int]:
    query = (
        select(Movie)
        .options(
            selectinload(Movie.director),
            selectinload(Movie.genres),
            selectinload(Movie.actors),
        )
    )

    count_query = select(func.count(Movie.id))

    if search:
        search_filter = Movie.title.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if genre_id is not None:
        genre_filter = Movie.genres.any(
            Genre.id == genre_id,
        )
        query = query.where(genre_filter)
        count_query = count_query.where(genre_filter)

    if release_year is not None:
        query = query.where(
            Movie.release_year == release_year,
        )
        count_query = count_query.where(
            Movie.release_year == release_year,
        )

    sort_column = {
        "title": Movie.title,
        "release_year": Movie.release_year,
        "rating": Movie.rating,
        "price": Movie.price,
        "created_at": Movie.created_at,
    }.get(sort_by, Movie.created_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * per_page

    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)

    movies = list(
        result.scalars().unique().all(),
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    return movies, total
