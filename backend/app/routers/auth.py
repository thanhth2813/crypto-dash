from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest) -> UserResponse:
    # Placeholder — real logic in AUTH-002
    return UserResponse(id="placeholder", email=req.email)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest) -> TokenResponse:
    # Placeholder — real logic in AUTH-002
    return TokenResponse(access_token="access.placeholder", refresh_token="refresh.placeholder")


@router.post("/refresh", response_model=TokenResponse)
def refresh() -> TokenResponse:
    # Placeholder — real logic in AUTH-003
    return TokenResponse(access_token="access.placeholder", refresh_token="refresh.placeholder")


@router.post("/logout")
def logout() -> dict:
    # Placeholder — real logic in AUTH-003
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(payload: dict = Depends(get_current_user)) -> UserResponse:
    # Placeholder — real logic in AUTH-002
    return UserResponse(id=str(payload.get("sub")), email="placeholder@example.com")
