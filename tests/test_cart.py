from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.models.actor import Actor
from src.models.director import Director
from src.models.genre import Genre
from src.models.order import Cart, CartItem


@pytest.fixture
async def cart_auth(client: AsyncClient, activate_user):
    email = f"cart_{uuid4().hex}@example.com"
    password = "password123"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }


@pytest.fixture
async def cart_movie(
    client: AsyncClient,
    cart_auth,
    db_session,
):
    headers = cart_auth["headers"]

    genre = Genre(name=f"Cart Action {uuid4().hex[:8]}")
    actor = Actor(name=f"Cart Actor {uuid4().hex[:8]}")
    director = Director(name=f"Cart Director {uuid4().hex[:8]}")

    db_session.add_all([genre, actor, director])
    await db_session.commit()

    await db_session.refresh(genre)
    await db_session.refresh(actor)
    await db_session.refresh(director)

    response = await client.post(
        "/movies",
        headers=headers,
        json={
            "title": f"Cart Test Movie {uuid4().hex[:8]}",
            "description": "Movie for cart tests",
            "release_year": 2025,
            "duration_minutes": 120,
            "rating": "8.0",
            "price": "10.00",
            "director_id": director.id,
            "genre_ids": [genre.id],
            "actor_ids": [actor.id],
        },
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.asyncio
async def test_add_movie_to_cart(
    client: AsyncClient,
    cart_auth,
    cart_movie,
    db_session,
):
    headers = cart_auth["headers"]
    movie_id = cart_movie["id"]

    response = await client.post(
        f"/cart/{movie_id}",
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Movie added to cart",
    }

    result = await db_session.execute(
        select(Cart)
    )
    cart = result.scalar_one()

    result = await db_session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == movie_id,
        )
    )
    item = result.scalar_one()

    assert item.movie_id == movie_id


@pytest.mark.asyncio
async def test_get_cart(
    client: AsyncClient,
    cart_auth,
    cart_movie,
):
    headers = cart_auth["headers"]
    movie_id = cart_movie["id"]

    await client.post(
        f"/cart/{movie_id}",
        headers=headers,
    )

    response = await client.get(
        "/cart",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["movie_id"] == movie_id
    assert data["items"][0]["movie_title"] == cart_movie["title"]
    assert Decimal(data["items"][0]["price"]) == Decimal("10.00")
    assert Decimal(data["total_amount"]) == Decimal("10.00")


@pytest.mark.asyncio
async def test_remove_movie_from_cart(
    client: AsyncClient,
    cart_auth,
    cart_movie,
):
    headers = cart_auth["headers"]
    movie_id = cart_movie["id"]

    add_response = await client.post(
        f"/cart/{movie_id}",
        headers=headers,
    )

    assert add_response.status_code == 201

    response = await client.delete(
        f"/cart/{movie_id}",
        headers=headers,
    )

    assert response.status_code == 204

    response = await client.get(
        "/cart",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert Decimal(
        response.json()["total_amount"]
    ) == Decimal("0.00")


@pytest.mark.asyncio
async def test_add_nonexistent_movie_to_cart(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.post(
        "/cart/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_add_same_movie_twice_to_cart(
    client: AsyncClient,
    cart_auth,
    cart_movie,
):
    headers = cart_auth["headers"]
    movie_id = cart_movie["id"]

    first_response = await client.post(
        f"/cart/{movie_id}",
        headers=headers,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        f"/cart/{movie_id}",
        headers=headers,
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Movie is already in cart"
    )


@pytest.mark.asyncio
async def test_remove_movie_not_in_cart(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.delete(
        "/cart/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found"
