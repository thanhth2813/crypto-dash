from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from ..services.auth_service import AuthService
from ..utils.redis import check_login_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        access_token, refresh_token, user = await AuthService.register(db=db, req=req)
    except ValueError:
        # 409 if email already exists, but keep message generic
        raise HTTPException(status_code=409, detail="registration failed")

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(id=user.id, email=user.email),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    ip = request.client.host if request.client else "unknown"
    email = req.email.strip().lower()

    allowed, retry_after = await check_login_rate_limit(ip=ip, email=email)
    if not allowed:
        if retry_after is not None:
            response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(status_code=429, detail="too many attempts")

    result = await AuthService.login(db=db, req=req)
    if result is None:
        raise HTTPException(status_code=401, detail="invalid credentials")

    access_token, refresh_token, user = result
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(id=user.id, email=user.email),
    )


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)
