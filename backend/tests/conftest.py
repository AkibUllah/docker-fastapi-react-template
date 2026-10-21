from __future__ import annotations

from collections.abc import AsyncIterator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.cache import TokenDenylist
from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine, create_session_factory
from app.main import create_app
from app.schemas.user import UserCreate
from app.services.user_service import UserService


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        env="test",
        secret_key="unit-test-secret-key-0123456789-abcdef",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url=None,
        access_token_expire_minutes=5,
        log_json=False,
        _env_file=None,
    )


@pytest.fixture
async def app(settings: Settings):
    """App wired to an in-memory SQLite database and a fakeredis denylist."""
    application = create_app(settings)
    engine = create_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    application.state.settings = settings
    application.state.engine = engine
    application.state.session_factory = create_session_factory(engine)
    application.state.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    application.state.denylist = TokenDenylist(application.state.redis)
    application.router.lifespan_context = _noop_lifespan  # state is set up here, not by lifespan
    yield application
    await engine.dispose()


from contextlib import asynccontextmanager  # noqa: E402


@asynccontextmanager
async def _noop_lifespan(app):  # noqa: ANN001, ANN201
    yield


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def superuser(app):
    async with app.state.session_factory() as db:
        return await UserService(db).create(
            UserCreate(
                email="admin@example.com",
                password="admin12345",
                full_name="Admin",
                is_superuser=True,
            )
        )


@pytest.fixture
async def user(app):
    async with app.state.session_factory() as db:
        return await UserService(db).create(
            UserCreate(email="akib@example.com", password="secret123", full_name="Akib Jafor")
        )


async def login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def bearer(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def user_headers(client, user) -> dict[str, str]:
    return bearer(await login(client, "akib@example.com", "secret123"))


@pytest.fixture
async def admin_headers(client, superuser) -> dict[str, str]:
    return bearer(await login(client, "admin@example.com", "admin12345"))
