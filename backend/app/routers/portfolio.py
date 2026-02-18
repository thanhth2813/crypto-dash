from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary")
async def summary() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/holdings")
async def list_holdings() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented")
