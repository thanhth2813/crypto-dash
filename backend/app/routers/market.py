from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/prices")
async def prices() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/history")
async def history() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")
