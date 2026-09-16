from decimal import Decimal

import pytest
from sqlalchemy import select

from src.core.security import create_access_token
from src.models.actor import Actor
from src.models.director import Director
from src.models.genre import Genre
from src.models.movie import Movie
from src.models.user import User


@pytest.fixture
async def auth_headers(db_session):
    user = User(
        email="movie-test@example.com",
        hashed_password="test-password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def movie_relations(db_session):
    genre = Genre(name="Action")
    actor = Actor(name="Test Actor")
    director = Director(name="Test Director")

    db_session.add_all([genre, actor, director])
    await db_session.commit()

    await db_session.refresh(genre)
    await db_session.refresh(actor)
    await db_session.refresh(director)

    return genre, actor, director


@pytest.fixture
async def movie_data(movie_relations):
    genre, actor, director = movie_relations

    return {
        "title": "The Matrix",
        "description": "A science fiction movie",
        "release_year": 1999,
        "duration_minutes": 136,
        "rating": "8.7",
        "price": "12.99",
        "director_id": director.id,
        "genre_ids": [genre.id],
        "actor_ids": [actor.id],
    }


@pytest.mark.asyncio
async def test_get_movies_empty(client):
    response = await client.get("/movies")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["pages"] == 0


@pytest.mark.asyncio
async def test_create_movie_requires_auth(client, movie_data):
    response = await client.post(
        "/movies",
        json=movie_data,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_movie(
    client,
    auth_headers,
    movie_data,
):
    response = await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "The Matrix"
    assert data["release_year"] == 1999
    assert data["duration_minutes"] == 136
    assert data["rating"] == "8.7"
    assert data["price"] == "12.99"
    assert data["director"]["name"] == "Test Director"
    assert data["genres"][0]["name"] == "Action"
    assert data["actors"][0]["name"] == "Test Actor"


@pytest.mark.asyncio
async def test_create_movie_invalid_director(
    client,
    auth_headers,
):
    data = {
        "title": "Invalid Movie",
        "release_year": 2024,
        "duration_minutes": 100,
        "rating": "7.0",
        "price": "10.00",
        "director_id": 99999,
    }

    response = await client.post(
        "/movies",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Director not found"


@pytest.mark.asyncio
async def test_get_movie(
    client,
    auth_headers,
    movie_data,
):
    create_response = await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    movie_id = create_response.json()["id"]

    response = await client.get(
        f"/movies/{movie_id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == movie_id
    assert response.json()["title"] == "The Matrix"


@pytest.mark.asyncio
async def test_get_movie_not_found(client):
    response = await client.get("/movies/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_update_movie(
    client,
    auth_headers,
    movie_data,
):
    create_response = await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    movie_id = create_response.json()["id"]

    response = await client.patch(
        f"/movies/{movie_id}",
        json={
            "title": "The Matrix Reloaded",
            "price": "15.99",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "The Matrix Reloaded"
    assert data["price"] == "15.99"


@pytest.mark.asyncio
async def test_delete_movie(
    client,
    auth_headers,
    movie_data,
):
    create_response = await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    movie_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/movies/{movie_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/movies/{movie_id}",
    )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_movies(
    client,
    auth_headers,
    movie_data,
):
    await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    response = await client.get(
        "/movies?search=Matrix",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "The Matrix"


@pytest.mark.asyncio
async def test_filter_movies_by_genre(
    client,
    auth_headers,
    movie_data,
    movie_relations,
):
    genre, _, _ = movie_relations

    await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    response = await client.get(
        f"/movies?genre_id={genre.id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "The Matrix"


@pytest.mark.asyncio
async def test_filter_movies_by_release_year(
    client,
    auth_headers,
    movie_data,
):
    await client.post(
        "/movies",
        json=movie_data,
        headers=auth_headers,
    )

    response = await client.get(
        "/movies?release_year=1999",
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_sort_movies(
    client,
    auth_headers,
):
    movies = [
        {
            "title": "Z Movie",
            "release_year": 2020,
            "duration_minutes": 100,
            "rating": "6.0",
            "price": "10.00",
        },
        {
            "title": "A Movie",
            "release_year": 2021,
            "duration_minutes": 100,
            "rating": "9.0",
            "price": "20.00",
        },
    ]

    for movie in movies:
        response = await client.post(
            "/movies",
            json=movie,
            headers=auth_headers,
        )
        assert response.status_code == 201

    response = await client.get(
        "/movies?sort_by=title&sort_order=asc",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["title"] == "A Movie"
    assert data["items"][1]["title"] == "Z Movie"


@pytest.mark.asyncio
async def test_movies_pagination(
    client,
    auth_headers,
):
    for number in range(3):
        response = await client.post(
            "/movies",
            json={
                "title": f"Movie {number}",
                "release_year": 2020 + number,
                "duration_minutes": 100,
                "rating": "7.0",
                "price": "10.00",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    response = await client.get(
        "/movies?page=1&per_page=2",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 2
