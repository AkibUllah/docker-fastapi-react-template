"""Start-up tasks that need the database: currently the optional first superuser."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.schemas.user import UserCreate
from app.services.user_service import EmailAlreadyRegisteredError, UserService

logger = logging.getLogger(__name__)


async def ensure_first_superuser(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> bool:
    """Create ``APP_FIRST_SUPERUSER_EMAIL`` as a superuser if both settings are present and the
    account does not exist yet. Returns True when a user was created. Safe to run on every start:
    an existing account (superuser or not) is left untouched, and a database that is not ready yet
    only logs a warning so the app still comes up."""
    email, password = settings.first_superuser_email, settings.first_superuser_password
    if not email or not password:
        return False
    try:
        async with session_factory() as db:
            service = UserService(db)
            if await service.get_by_email(email) is not None:
                return False
            await service.create(
                UserCreate(email=email, password=password, full_name="Administrator"),
                is_superuser=True,
            )
            return True
    except EmailAlreadyRegisteredError:
        return False
    except Exception:  # noqa: BLE001 - never block start-up on a bootstrap convenience
        logger.warning("first superuser not created", exc_info=True)
        return False
