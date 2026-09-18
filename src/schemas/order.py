from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    movie_id: int
    price: Decimal


class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
