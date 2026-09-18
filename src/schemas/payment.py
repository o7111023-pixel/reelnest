from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    status: PaymentStatus
    stripe_session_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentCreateResponse(BaseModel):
    payment_id: int
    order_id: int
    amount: Decimal
    status: PaymentStatus
    checkout_url: str
