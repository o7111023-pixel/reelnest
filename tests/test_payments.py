from decimal import Decimal
from unittest.mock import patch

import pytest
import stripe
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_payment(
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

    order_response = await client.post(
        "/orders",
        headers=headers,
    )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    mock_session = type(
        "MockStripeSession",
        (),
        {
            "id": "cs_test_123",
            "url": "https://checkout.stripe.com/test",
        },
    )()

    with patch(
        "src.services.payment.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        response = await client.post(
            f"/payments/{order_id}",
            headers=headers,
        )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_id"] > 0
    assert data["order_id"] == order_id
    assert Decimal(data["amount"]) == Decimal("10.00")
    assert data["status"] == "pending"
    assert data["checkout_url"] == (
        "https://checkout.stripe.com/test"
    )


@pytest.mark.asyncio
async def test_create_payment_order_not_found(
    client: AsyncClient,
    cart_auth,
):
    headers = cart_auth["headers"]

    response = await client.post(
        "/payments/999999",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_create_payment_for_non_pending_order(
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

    order_response = await client.post(
        "/orders",
        headers=headers,
    )

    order_id = order_response.json()["id"]

    status_response = await client.patch(
        f"/orders/{order_id}/status",
        headers=headers,
        json={
            "status": "paid",
        },
    )

    assert status_response.status_code == 200

    mock_session = type(
        "MockStripeSession",
        (),
        {
            "id": "cs_test_456",
            "url": "https://checkout.stripe.com/test",
        },
    )()

    with patch(
        "src.services.payment.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        response = await client.post(
            f"/payments/{order_id}",
            headers=headers,
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order is not pending"
    )


@pytest.mark.asyncio
async def test_create_payment_twice(
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

    order_response = await client.post(
        "/orders",
        headers=headers,
    )

    order_id = order_response.json()["id"]

    mock_session = type(
        "MockStripeSession",
        (),
        {
            "id": "cs_test_789",
            "url": "https://checkout.stripe.com/test",
        },
    )()

    with patch(
        "src.services.payment.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        first_response = await client.post(
            f"/payments/{order_id}",
            headers=headers,
        )

    assert first_response.status_code == 201

    with patch(
        "src.services.payment.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        second_response = await client.post(
            f"/payments/{order_id}",
            headers=headers,
        )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Payment already exists"
    )


@pytest.mark.asyncio
async def test_stripe_webhook_payment_completed(
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

    order_response = await client.post(
        "/orders",
        headers=headers,
    )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    mock_session = type(
        "MockStripeSession",
        (),
        {
            "id": "cs_webhook_test",
            "url": "https://checkout.stripe.com/test",
        },
    )()

    with patch(
        "src.services.payment.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        payment_response = await client.post(
            f"/payments/{order_id}",
            headers=headers,
        )

    assert payment_response.status_code == 201

    webhook_event = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_webhook_test",
            },
        },
    }

    with patch(
        "src.services.payment.stripe.Webhook.construct_event",
        return_value=webhook_event,
    ):
        response = await client.post(
            "/payments/webhook",
            headers={
                "Stripe-Signature": "test_signature",
            },
            content=b"test_payload",
        )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Webhook processed",
    }

    order_response = await client.get(
        f"/orders/{order_id}",
        headers=headers,
    )

    assert order_response.status_code == 200
    assert order_response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature(
    client: AsyncClient,
):
    with patch(
        "src.services.payment.stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError(
            "Invalid signature",
            "test",
        ),
    ):
        response = await client.post(
            "/payments/webhook",
            headers={
                "Stripe-Signature": "invalid_signature",
            },
            content=b"invalid_payload",
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid webhook signature"
    )
