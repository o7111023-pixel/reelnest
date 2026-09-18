from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.user import User
from src.schemas.cart import CartResponse
from src.core.security import get_current_user
from src.services.cart import (
    add_movie_to_cart,
    calculate_cart_total,
    get_cart,
    remove_movie_from_cart,
)

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get(
    "",
    response_model=CartResponse,
    summary="Get current user's cart",
)
async def get_current_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    cart, items = await get_cart(db, current_user.id)

    if cart is None:
        return CartResponse(
            id=0,
            items=[],
            total_amount=0,
        )

    return CartResponse(
        id=cart.id,
        items=[
            {
                "id": item.id,
                "movie_id": movie.id,
                "movie_title": movie.title,
                "price": movie.price,
            }
            for item, movie in items
        ],
        total_amount=calculate_cart_total(items),
    )


@router.post(
    "/{movie_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to cart",
)
async def add_to_cart(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await add_movie_to_cart(
        db=db,
        user_id=current_user.id,
        movie_id=movie_id,
    )

    return {"message": "Movie added to cart"}


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove movie from cart",
)
async def remove_from_cart(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await remove_movie_from_cart(
        db=db,
        user_id=current_user.id,
        movie_id=movie_id,
    )
