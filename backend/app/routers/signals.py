from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
async def get_signals() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")
