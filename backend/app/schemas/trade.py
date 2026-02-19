"""Trade history schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TradeResponse(BaseModel):
    """Trade order response for history."""
    id: int
    bot_id: int
    bot_name: str | None
    exchange: str
    symbol: str
    side: str
    order_type: str
    amount: float
    price: float | None
    filled_amount: float
    filled_price: float | None
    status: str
    fee: float
    fee_currency: str | None
    created_at: datetime
    executed_at: datetime | None
    
    class Config:
        from_attributes = True


class TradeSummary(BaseModel):
    """Trade history summary statistics."""
    total_trades: int
    total_buy: int
    total_sell: int
    total_volume: float  # Total amount traded
    total_fees: float
    total_pnl: float
    win_rate: float  # Percentage of profitable trades (simplified)
