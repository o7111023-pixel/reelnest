from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.schemas.payment import PaymentCreateResponse
from src.services.payment import create_payment


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/{order_id}",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe payment",
    description=(
        "Creates a Stripe Checkout Session for the user's pending order "
        "and returns the checkout URL."
    ),
)
async def create_order_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentCreateResponse:
    payment, checkout_url = await create_payment(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )

    return PaymentCreateResponse(
        payment_id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        status=payment.status,
        checkout_url=checkout_url,
    )
