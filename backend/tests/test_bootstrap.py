"""Settings normalisation and the start-up superuser bootstrap."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.bootstrap import ensure_first_superuser
from app.services.user_service import UserService


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
        ("postgresql+asyncpg://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
        ("sqlite+aiosqlite:///:memory:", "sqlite+aiosqlite:///:memory:"),
    ],
)
def test_database_url_is_routed_through_asyncpg(given: str, expected: str) -> None:
    settings = Settings(
        database_url=given, secret_key="unit-test-secret-key-0123456789-abcdef", _env_file=None
    )
    assert settings.database_url == expected


def _with_superuser(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "first_superuser_email": "boot@example.com",
            "first_superuser_password": "Bootstrap123",
        }
    )


async def test_bootstrap_creates_superuser_once(app, settings: Settings) -> None:
    configured = _with_superuser(settings)
    assert await ensure_first_superuser(configured, app.state.session_factory) is True
    assert await ensure_first_superuser(configured, app.state.session_factory) is False
    async with app.state.session_factory() as db:
        user = await UserService(db).get_by_email("boot@example.com")
    assert user is not None and user.is_superuser


async def test_bootstrap_is_a_noop_without_settings(app, settings: Settings) -> None:
    assert settings.first_superuser_email is None
    assert await ensure_first_superuser(settings, app.state.session_factory) is False


async def test_bootstrap_leaves_existing_account_alone(app, settings: Settings, user) -> None:
    configured = settings.model_copy(
        update={"first_superuser_email": user.email, "first_superuser_password": "Another123"}
    )
    assert await ensure_first_superuser(configured, app.state.session_factory) is False
    async with app.state.session_factory() as db:
        refreshed = await UserService(db).get_by_email(user.email)
    assert refreshed is not None and refreshed.is_superuser is False
