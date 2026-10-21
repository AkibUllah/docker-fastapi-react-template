#!/usr/bin/env python
"""Create (or promote) a superuser.

    python scripts/create_superuser.py admin@example.com 'S3cure-pass'
    APP_FIRST_SUPERUSER_EMAIL=... APP_FIRST_SUPERUSER_PASSWORD=... python scripts/create_superuser.py

Run from the backend directory (or inside the backend container, where it is mounted
at /scripts) so that the ``app`` package and ``.env`` resolve.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, "/app")

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_engine, create_session_factory  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services.user_service import EmailAlreadyRegisteredError, UserService  # noqa: E402


async def main(email: str, password: str) -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        async with create_session_factory(engine)() as db:
            service = UserService(db)
            existing = await service.get_by_email(email)
            if existing is not None:
                if existing.is_superuser:
                    print(f"{email} is already a superuser")
                    return 0
                existing.is_superuser = True
                await db.commit()
                print(f"promoted {email} to superuser")
                return 0
            try:
                await service.create(
                    UserCreate(email=email, password=password, full_name="Administrator", is_superuser=True)
                )
            except EmailAlreadyRegisteredError:
                print(f"{email} already exists", file=sys.stderr)
                return 1
            print(f"created superuser {email}")
            return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    settings = get_settings()
    if len(sys.argv) == 3:
        email, password = sys.argv[1], sys.argv[2]
    elif settings.first_superuser_email and settings.first_superuser_password:
        email, password = settings.first_superuser_email, settings.first_superuser_password
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(asyncio.run(main(email, password)))
