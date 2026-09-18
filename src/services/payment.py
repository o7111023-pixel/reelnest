from decimal import Decimal

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.order import Order, OrderStatus
from src.models.payment import Payment, PaymentStatus


async def create_payment(
    db: AsyncSession,
    user_id: int,
    order_id: int,
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
    )

    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Order is not pending",
        )

    payment_result = await db.execute(
        select(Payment).where(
            Payment.order_id == order.id,
        )
    )

    existing_payment = payment_result.scalar_one_or_none()

    if existing_payment is not None:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists",
        )

    stripe.api_key = settings.stripe_secret_key

    amount_in_cents = int(
        Decimal(order.total_amount) * 100
    )

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"ReelNest Order #{order.id}",
                    },
                    "unit_amount": amount_in_cents,
                },
                "quantity": 1,
            }
        ],
        success_url=(
            f"{settings.frontend_url}"
            f"/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        ),
        cancel_url=(
            f"{settings.frontend_url}"
            f"/payment/cancel"
        ),
    )

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        status=PaymentStatus.PENDING,
        stripe_session_id=session.id,
    )

    db.add(payment)

    await db.commit()
    await db.refresh(payment)

    return payment, session.url


async def handle_stripe_webhook(
    db: AsyncSession,
    payload: bytes,
    signature: str,
):
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload",
        ) from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature",
        ) from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        stripe_session_id = session["id"]

        result = await db.execute(
            select(Payment).where(
                Payment.stripe_session_id
                == stripe_session_id
            )
        )

        payment = result.scalar_one_or_none()

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        payment.status = PaymentStatus.PAID

        order_result = await db.execute(
            select(Order).where(
                Order.id == payment.order_id
            )
        )

        order = order_result.scalar_one_or_none()

        if order is not None:
            order.status = OrderStatus.PAID

        await db.commit()

    return {"message": "Webhook processed"}
