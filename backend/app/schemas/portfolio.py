from __future__ import annotations

from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    coin_id: str
    symbol: str
    amount: float = Field(gt=0)
    buy_price: float = Field(gt=0)


class HoldingUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    buy_price: float | None = Field(default=None, gt=0)


class HoldingResponse(BaseModel):
    id: int
    coin_id: str
    symbol: str
    amount: float
    buy_price: float


class HoldingWithPnlResponse(HoldingResponse):
    current_price: float
    pnl: float


class AllocationItem(BaseModel):
    coin_id: str
    symbol: str
    value: float
    weight: float


class PortfolioSummary(BaseModel):
    total_invested: float
    total_value: float
    total_pnl: float
    allocation: list[AllocationItem]
