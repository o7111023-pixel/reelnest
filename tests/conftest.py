import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.database import Base, get_db
from src.main import app


TEST_DATABASE_URL = (
    "postgresql+asyncpg://reelnest:reelnest@localhost:5433/reelnest_test"
)


@pytest.fixture
async def db_session():
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def activate_user(db_session):
    async def _activate_user(email: str):
        from src.models.user import User

        result = await db_session.execute(
            select(User).where(User.email == email),
        )

        user = result.scalar_one()

        user.is_active = True

        await db_session.commit()
        await db_session.refresh(user)

        return user

    return _activate_user


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
