from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CartItemResponse(BaseModel):
    id: int
    movie_id: int
    movie_title: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    items: list[CartItemResponse]
    total_amount: Decimal
