from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movie import Movie
from src.models.order import Cart, CartItem


async def get_or_create_cart(
    db: AsyncSession,
    user_id: int,
) -> Cart:
    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()

    return cart


async def add_movie_to_cart(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> CartItem:
    movie_result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    movie = movie_result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    cart = await get_or_create_cart(db, user_id)

    item_result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == movie_id,
        )
    )
    existing_item = item_result.scalar_one_or_none()

    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in cart",
        )

    item = CartItem(
        cart_id=cart.id,
        movie_id=movie_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return item


async def remove_movie_from_cart(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
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
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == movie_id,
        )
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie is not in cart",
        )

    await db.delete(item)
    await db.commit()


async def get_cart(
    db: AsyncSession,
    user_id: int,
) -> tuple[Cart | None, list[tuple[CartItem, Movie]]]:
    cart_result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )
    cart = cart_result.scalar_one_or_none()

    if cart is None:
        return None, []

    result = await db.execute(
        select(CartItem, Movie)
        .join(Movie, Movie.id == CartItem.movie_id)
        .where(CartItem.cart_id == cart.id)
    )

    return cart, list(result.all())


def calculate_cart_total(
    items: list[tuple[CartItem, Movie]],
) -> Decimal:
    return sum(
        (movie.price for _, movie in items),
        Decimal("0.00"),
    )
