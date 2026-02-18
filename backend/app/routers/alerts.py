from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")
