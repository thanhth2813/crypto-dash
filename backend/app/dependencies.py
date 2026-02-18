from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .services.auth_service import AuthService
from .utils.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if creds is None:
        raise HTTPException(status_code=401, detail="invalid token")

    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="invalid token")

    sub = payload.get("sub")
    try:
        user_id = int(sub)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="invalid token")

    user = await AuthService.get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid token")

    return user
