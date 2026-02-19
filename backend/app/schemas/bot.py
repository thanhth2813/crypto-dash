"""Bot schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BotCreate(BaseModel):
    """Create a new trading bot."""
    name: str = Field(..., min_length=1, max_length=100)
    strategy: str = Field(..., pattern="^(dca|grid|signal)$")
    exchange: str = Field(default="paper", pattern="^(binance|paper)$")
    symbol: str = Field(..., min_length=1, max_length=20)
    config: dict = Field(default_factory=dict)
    paper_mode: bool = Field(default=True)


class BotUpdate(BaseModel):
    """Update bot configuration."""
    name: str | None = Field(None, min_length=1, max_length=100)
    config: dict | None = None


class BotResponse(BaseModel):
    """Bot response."""
    id: int
    user_id: int
    name: str
    strategy: str
    exchange: str
    symbol: str
    config: dict
    status: str
    paper_mode: bool
    total_invested: float
    total_pnl: float
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None
    
    class Config:
        from_attributes = True


class TradeOrderResponse(BaseModel):
    """Trade order response."""
    id: int
    bot_id: int
    exchange: str
    symbol: str
    side: str
    order_type: str
    amount: float
    price: float | None
    filled_amount: float
    filled_price: float | None
    status: str
    exchange_order_id: str | None
    fee: float
    fee_currency: str | None
    created_at: datetime
    executed_at: datetime | None
    
    class Config:
        from_attributes = True


class BotDetailResponse(BotResponse):
    """Bot detail with recent orders."""
    recent_orders: list[TradeOrderResponse] = Field(default_factory=list)
