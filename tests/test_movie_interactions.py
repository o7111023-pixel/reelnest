from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token
from src.models.movie import Movie


async def create_test_movie(db_session: AsyncSession) -> Movie:
    movie = Movie(
        title="Test Movie",
        description="Test description",
        release_year=2025,
        duration_minutes=120,
        price=9.99,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


async def create_auth_headers(db_session: AsyncSession) -> dict[str, str]:
    from src.models.user import User

    user = User(
        email="interaction@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)

    return {"Authorization": f"Bearer {token}"}


async def test_add_movie_to_favorites(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    response = await client.post(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Movie added to favorites",
    }


async def test_add_movie_to_favorites_requires_auth(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)

    response = await client.post(
        f"/movies/{movie.id}/favorite",
    )

    assert response.status_code == 401


async def test_add_nonexistent_movie_to_favorites(
    client: AsyncClient,
    db_session: AsyncSession,
):
    headers = await create_auth_headers(db_session)

    response = await client.post(
        "/movies/99999/favorite",
        headers=headers,
    )

    assert response.status_code == 404


async def test_add_movie_to_favorites_twice(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    first_response = await client.post(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )
    second_response = await client.post(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_remove_movie_from_favorites(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    await client.post(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )

    response = await client.delete(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Movie removed from favorites",
    }


async def test_remove_movie_from_favorites_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    response = await client.delete(
        f"/movies/{movie.id}/favorite",
        headers=headers,
    )

    assert response.status_code == 404


async def test_remove_movie_from_favorites_requires_auth(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)

    response = await client.delete(
        f"/movies/{movie.id}/favorite",
    )

    assert response.status_code == 401


async def test_like_movie(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    response = await client.post(
        f"/movies/{movie.id}/like",
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Movie liked",
    }


async def test_like_movie_requires_auth(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)

    response = await client.post(
        f"/movies/{movie.id}/like",
    )

    assert response.status_code == 401


async def test_like_nonexistent_movie(
    client: AsyncClient,
    db_session: AsyncSession,
):
    headers = await create_auth_headers(db_session)

    response = await client.post(
        "/movies/99999/like",
        headers=headers,
    )

    assert response.status_code == 404


async def test_like_movie_twice(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    first_response = await client.post(
        f"/movies/{movie.id}/like",
        headers=headers,
    )
    second_response = await client.post(
        f"/movies/{movie.id}/like",
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_unlike_movie(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    await client.post(
        f"/movies/{movie.id}/like",
        headers=headers,
    )

    response = await client.delete(
        f"/movies/{movie.id}/like",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Movie unliked",
    }


async def test_unlike_movie_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)
    headers = await create_auth_headers(db_session)

    response = await client.delete(
        f"/movies/{movie.id}/like",
        headers=headers,
    )

    assert response.status_code == 404


async def test_unlike_movie_requires_auth(
    client: AsyncClient,
    db_session: AsyncSession,
):
    movie = await create_test_movie(db_session)

    response = await client.delete(
        f"/movies/{movie.id}/like",
    )

    assert response.status_code == 401
