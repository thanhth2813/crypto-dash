from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest) -> UserResponse:
    # Placeholder — real logic later
    return UserResponse(id="placeholder", email=req.email)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest) -> TokenResponse:
    # Placeholder — real logic later
    return TokenResponse(access_token="access.placeholder", refresh_token="refresh.placeholder")


@router.get("/me", response_model=UserResponse)
async def me() -> UserResponse:
    # Placeholder — real logic later
    raise HTTPException(status_code=501, detail="Not implemented")
