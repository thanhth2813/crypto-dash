from __future__ import annotations

from pydantic import BaseModel


class SignalResponse(BaseModel):
    coin_id: str
    symbol: str
    signal: str  # BUY|SELL|HOLD
    rsi: float | None = None
    ema_short: float | None = None
    ema_long: float | None = None
    confidence: float | None = None
