from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.db.database import Base, get_db
from src.main import app
from src.models.actor import Actor
from src.models.director import Director
from src.models.genre import Genre


TEST_DATABASE_URL = (
    "postgresql+asyncpg://reelnest:reelnest"
    "@localhost:5433/reelnest_test"
)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def activate_user(db_session):
    async def _activate_user(email: str):
        from src.models.user import User

        result = await db_session.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one()

        user.is_active = True

        await db_session.commit()
        await db_session.refresh(user)

        return user

    return _activate_user


@pytest_asyncio.fixture
async def cart_auth(
    client: AsyncClient,
    activate_user,
):
    email = f"cart_{uuid4().hex}@example.com"
    password = "password123"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    await activate_user(email)

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }


@pytest_asyncio.fixture
async def cart_movie(
    client: AsyncClient,
    cart_auth,
    db_session,
):
    headers = cart_auth["headers"]

    genre = Genre(
        name=f"Cart Action {uuid4().hex[:8]}"
    )

    actor = Actor(
        name=f"Cart Actor {uuid4().hex[:8]}"
    )

    director = Director(
        name=f"Cart Director {uuid4().hex[:8]}"
    )

    db_session.add_all(
        [
            genre,
            actor,
            director,
        ]
    )

    await db_session.commit()

    await db_session.refresh(genre)
    await db_session.refresh(actor)
    await db_session.refresh(director)

    response = await client.post(
        "/movies",
        headers=headers,
        json={
            "title": f"Cart Test Movie {uuid4().hex[:8]}",
            "description": "Movie for cart tests",
            "release_year": 2025,
            "duration_minutes": 120,
            "rating": "8.0",
            "price": "10.00",
            "director_id": director.id,
            "genre_ids": [genre.id],
            "actor_ids": [actor.id],
        },
    )

    assert response.status_code == 201

    return response.json()
