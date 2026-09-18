from decimal import Decimal

from pydantic import BaseModel, Field


class InteractionResponse(BaseModel):
    message: str


class MovieRatingCreate(BaseModel):
    rating: Decimal = Field(
        ge=1,
        le=10,
        decimal_places=1,
        max_digits=3,
    )


class MovieRatingResponse(BaseModel):
    rating: Decimal
    movie_rating: Decimal
