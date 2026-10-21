from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import CurrentSuperuser, CurrentUser, get_user_service
from app.db.models import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import EmailAlreadyRegisteredError, UserService

router = APIRouter(prefix="/users", tags=["users"])


async def _get_or_404(users: UserService, user_id: uuid.UUID) -> User:
    user = await users.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=Page[UserRead])
async def list_users(
    _: CurrentSuperuser,
    users: Annotated[UserService, Depends(get_user_service)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> Page[UserRead]:
    items, total = await users.list(offset=offset, limit=limit)
    return Page(
        items=[UserRead.model_validate(u) for u in items], total=total, offset=offset, limit=limit
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: CurrentSuperuser,
    users: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    try:
        return UserRead.model_validate(await users.create(payload))
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current: CurrentUser,
    users: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    if user_id != current.id and not current.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return UserRead.model_validate(await _get_or_404(users, user_id))


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current: CurrentUser,
    users: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    if user_id != current.id and not current.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if not current.is_superuser and (
        payload.is_superuser is not None or payload.is_active is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change role or status"
        )
    user = await _get_or_404(users, user_id)
    try:
        return UserRead.model_validate(await users.update(user, payload))
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current: CurrentSuperuser,
    users: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    if user_id == current.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )
    await users.delete(await _get_or_404(users, user_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
