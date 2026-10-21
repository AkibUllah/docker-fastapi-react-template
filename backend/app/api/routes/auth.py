from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_denylist, get_settings_dep, get_user_service
from app.core.cache import TokenDenylist
from app.core.config import Settings
from app.core.security import TokenError, create_token, decode_token, seconds_until
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPair
from app.schemas.common import Message
from app.schemas.user import UserRead, UserRegister
from app.services.user_service import EmailAlreadyRegisteredError, UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_tokens(user_id: uuid.UUID, settings: Settings) -> TokenPair:
    access, _ = create_token(str(user_id), "access", settings)
    refresh, _ = create_token(str(user_id), "refresh", settings)
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister, users: Annotated[UserService, Depends(get_user_service)]
) -> UserRead:
    try:
        user = await users.create(payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    users: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> TokenPair:
    user = await users.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return issue_tokens(user.id, settings)


@router.post("/refresh", response_model=TokenPair, summary="Rotate a refresh token")
async def refresh(
    payload: RefreshRequest,
    users: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    denylist: Annotated[TokenDenylist, Depends(get_denylist)],
) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, "refresh", settings)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if await denylist.is_revoked(claims["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token revoked"
        )
    user = await users.get(uuid.UUID(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing"
        )
    # Rotation: the presented refresh token is revoked and a fresh pair is issued.
    await denylist.revoke(claims["jti"], seconds_until(claims["exp"]))
    return issue_tokens(user.id, settings)


@router.post("/logout", response_model=Message)
async def logout(
    payload: LogoutRequest,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    denylist: Annotated[TokenDenylist, Depends(get_denylist)],
) -> Message:
    try:
        claims = decode_token(payload.refresh_token, "refresh", settings)
    except TokenError:
        return Message(detail="logged out")  # already unusable; nothing to revoke
    await denylist.revoke(claims["jti"], seconds_until(claims["exp"]))
    return Message(detail="logged out")


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
