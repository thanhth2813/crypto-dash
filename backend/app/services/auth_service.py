from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest
from ..utils.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    async def register(*, db: AsyncSession, req: RegisterRequest) -> tuple[str, User]:
        # normalize email (avoid duplicates by case)
        email = req.email.strip().lower()
        user = User(email=email, password_hash=hash_password(req.password))

        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Generic message; do not leak existence
            raise ValueError("registration_failed")

        await db.refresh(user)
        token = create_access_token(user_id=str(user.id))
        return token, user

    @staticmethod
    async def login(*, db: AsyncSession, req: LoginRequest) -> tuple[str, User] | None:
        email = req.email.strip().lower()

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        if not verify_password(req.password, user.password_hash):
            return None

        token = create_access_token(user_id=str(user.id))
        return token, user

    @staticmethod
    async def get_user_by_id(*, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
