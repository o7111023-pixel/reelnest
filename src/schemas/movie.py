from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class GenreResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ActorResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class DirectorResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    release_year: int = Field(ge=1888, le=2100)
    duration_minutes: int = Field(gt=0)
    poster_url: HttpUrl | None = None
    rating: Decimal = Field(default=Decimal("0.0"), ge=0, le=10)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    director_id: int | None = None
    genre_ids: list[int] = Field(default_factory=list)
    actor_ids: list[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    release_year: int | None = Field(default=None, ge=1888, le=2100)
    duration_minutes: int | None = Field(default=None, gt=0)
    poster_url: HttpUrl | None = None
    rating: Decimal | None = Field(default=None, ge=0, le=10)
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    director_id: int | None = None
    genre_ids: list[int] | None = None
    actor_ids: list[int] | None = None


class MovieResponse(BaseModel):
    id: int
    title: str
    description: str | None
    release_year: int
    duration_minutes: int
    poster_url: HttpUrl | None
    rating: Decimal
    price: Decimal
    director: DirectorResponse | None
    genres: list[GenreResponse]
    actors: list[ActorResponse]

    model_config = {"from_attributes": True}


class MovieListResponse(BaseModel):
    items: list[MovieResponse]
    total: int
    page: int
    per_page: int
    pages: int
