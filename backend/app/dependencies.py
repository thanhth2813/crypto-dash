from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    return payload
