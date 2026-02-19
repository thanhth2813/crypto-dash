from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.refresh_token import RefreshToken
from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest
from ..utils.security import create_access_token, create_refresh_token, hash_password, verify_password

logger = logging.getLogger(__name__)


def _hash_token(token: str) -> str:
    # Store only a one-way hash of refresh token
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    @staticmethod
    async def register(*, db: AsyncSession, req: RegisterRequest) -> tuple[str, str, User]:
        email = req.email.strip().lower()
        user = User(email=email, password_hash=hash_password(req.password))

        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ValueError("registration_failed")

        await db.refresh(user)

        access_token = create_access_token(user_id=str(user.id))
        refresh_token = create_refresh_token(user_id=str(user.id))

        now = datetime.now(timezone.utc)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            expires_at=now + timedelta(days=7),
            revoked_at=None,
        )
        db.add(rt)
        await db.commit()

        return access_token, refresh_token, user

    @staticmethod
    async def login(*, db: AsyncSession, req: LoginRequest) -> tuple[str, str, User] | None:
        email = req.email.strip().lower()

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        if not verify_password(req.password, user.password_hash):
            return None

        access_token = create_access_token(user_id=str(user.id))
        refresh_token = create_refresh_token(user_id=str(user.id))

        now = datetime.now(timezone.utc)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            expires_at=now + timedelta(days=7),
            revoked_at=None,
        )
        db.add(rt)
        await db.commit()

        return access_token, refresh_token, user

    @staticmethod
    async def get_user_by_id(*, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
