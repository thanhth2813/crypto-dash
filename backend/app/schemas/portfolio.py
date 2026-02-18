from __future__ import annotations

from pydantic import BaseModel


class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    avg_price: float


class HoldingUpdate(BaseModel):
    quantity: float | None = None
    avg_price: float | None = None


class HoldingResponse(BaseModel):
    id: str
    symbol: str
    quantity: float
    avg_price: float


class PortfolioSummary(BaseModel):
    total_value: float
    pnl: float
