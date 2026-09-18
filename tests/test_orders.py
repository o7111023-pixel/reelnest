from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.models.order import Cart, CartItem, Order, OrderItem, OrderStatus


@pytest.mark.asyncio
async def test_create_order_from_cart(
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

    response = await client.post(
        "/orders",
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "pending"
    assert Decimal(data["total_amount"]) == Decimal("10.00")
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_order_with_empty_cart(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.post(
        "/orders",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found"


@pytest.mark.asyncio
async def test_get_orders(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    assert create_response.status_code == 201

    response = await client.get(
        "/orders",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "pending"
    assert Decimal(
        data["items"][0]["total_amount"]
    ) == Decimal("10.00")


@pytest.mark.asyncio
async def test_get_order(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    order_id = create_response.json()["id"]

    response = await client.get(
        f"/orders/{order_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["status"] == "pending"
    assert Decimal(data["total_amount"]) == Decimal("10.00")


@pytest.mark.asyncio
async def test_get_order_not_found(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.get(
        "/orders/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_cart_is_empty_after_order(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    assert create_response.status_code == 201

    response = await client.get(
        "/cart",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert Decimal(
        data["total_amount"]
    ) == Decimal("0.00")


@pytest.mark.asyncio
async def test_update_order_status_to_paid(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    response = await client.patch(
        f"/orders/{order_id}/status",
        headers=headers,
        json={
            "status": "paid",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["status"] == "paid"


@pytest.mark.asyncio
async def test_update_order_status_to_canceled(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    order_id = create_response.json()["id"]

    response = await client.patch(
        f"/orders/{order_id}/status",
        headers=headers,
        json={
            "status": "canceled",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["status"] == "canceled"


@pytest.mark.asyncio
async def test_update_order_status_invalid(
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

    create_response = await client.post(
        "/orders",
        headers=headers,
    )

    order_id = create_response.json()["id"]

    response = await client.patch(
        f"/orders/{order_id}/status",
        headers=headers,
        json={
            "status": "invalid_status",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_order_status_not_found(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.patch(
        "/orders/999999/status",
        headers=headers,
        json={
            "status": "paid",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
