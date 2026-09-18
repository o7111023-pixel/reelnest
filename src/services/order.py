from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movie import Movie
from src.models.order import Cart, CartItem, Order, OrderItem, OrderStatus


async def create_order_from_cart(
    db: AsyncSession,
    user_id: int,
) -> Order:
    cart_result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = cart_result.scalar_one_or_none()

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    result = await db.execute(
        select(CartItem, Movie)
        .join(Movie, Movie.id == CartItem.movie_id)
        .where(CartItem.cart_id == cart.id)
    )
    items = list(result.all())

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    total_amount = sum(
        (movie.price for _, movie in items),
        Decimal("0.00"),
    )

    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
    )

    db.add(order)
    await db.flush()

    for _, movie in items:
        order_item = OrderItem(
            order_id=order.id,
            movie_id=movie.id,
            price=movie.price,
        )
        db.add(order_item)

    await db.execute(
        delete(CartItem).where(
            CartItem.cart_id == cart.id,
        )
    )

    await db.commit()
    await db.refresh(order)

    return order


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    return list(result.scalars().all())


async def get_user_order(
    db: AsyncSession,
    user_id: int,
    order_id: int,
) -> Order:
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
    )

    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order
