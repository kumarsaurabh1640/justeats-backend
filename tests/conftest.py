"""
pytest conftest – creates all tables before each test and drops them after,
giving each test full isolation without session-scope event loop conflicts.

Set TEST_DATABASE_URL in .env or the environment to override the connection string.
"""
import os
from pathlib import Path

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env from the backend directory so TEST_DATABASE_URL is available
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Register every model with Base.metadata before create_all
import app.models.cart  # noqa: F401
import app.models.menu_item  # noqa: F401
import app.models.order  # noqa: F401
import app.models.refresh_token  # noqa: F401
import app.models.restaurant  # noqa: F401
import app.models.user  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/justeats_test",
)


# ── Function-scoped engine: create tables before each test, drop after ────────


@pytest_asyncio.fixture
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


# ── HTTP client with get_db overridden to use the test engine ─────────────────


@pytest_asyncio.fixture
async def client(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
