from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.schemas.order import OrderListResponse, OrderResponse
from src.services.order import (
    create_order_from_cart,
    get_user_order,
    get_user_orders,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    order = await create_order_from_cart(
        db=db,
        user_id=current_user.id,
    )

    return OrderResponse.model_validate(order)


@router.get(
    "",
    response_model=OrderListResponse,
    summary="Get current user's orders",
)
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderListResponse:
    orders = await get_user_orders(
        db=db,
        user_id=current_user.id,
    )

    return OrderListResponse(
        items=orders,
        total=len(orders),
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    order = await get_user_order(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )

    return OrderResponse.model_validate(order)
