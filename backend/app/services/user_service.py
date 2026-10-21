"""User persistence and authentication logic, independent of HTTP."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models import User
from app.schemas.user import UserCreate, UserRegister, UserUpdate


class EmailAlreadyRegisteredError(Exception):
    pass


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email.lower()))

    async def list(self, offset: int, limit: int) -> tuple[list[User], int]:
        total = await self.db.scalar(select(func.count()).select_from(User)) or 0
        rows = await self.db.scalars(
            select(User).order_by(User.created_at, User.email).offset(offset).limit(limit)
        )
        return list(rows), int(total)

    async def create(self, data: UserCreate | UserRegister, *, is_superuser: bool = False) -> User:
        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_superuser=is_superuser or getattr(data, "is_superuser", False),
        )
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise EmailAlreadyRegisteredError(data.email) from exc
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)
        if "password" in changes:
            user.hashed_password = hash_password(changes.pop("password"))
        if "email" in changes:
            changes["email"] = changes["email"].lower()
        for key, value in changes.items():
            setattr(user, key, value)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise EmailAlreadyRegisteredError(str(data.email)) from exc
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.hashed_password)
        ):
            return None
        return user
