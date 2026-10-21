"""FastAPI dependencies: settings, DB session, denylist, current user, authorisation."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TokenDenylist
from app.core.config import Settings
from app.core.security import TokenError, decode_token
from app.db.models import User
from app.services.user_service import UserService

bearer = HTTPBearer(auto_error=False)


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_denylist(request: Request) -> TokenDenylist:
    return request.app.state.denylist


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    session: AsyncSession = request.app.state.session_factory()
    try:
        yield session
    finally:
        await session.close()


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(db)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, "access", settings)
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) if isinstance(exc, TokenError) else "invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = await users.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(user: CurrentUser) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Superuser privileges required"
        )
    return user


CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
