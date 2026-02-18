from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PriceResponse(BaseModel):
    symbol: str
    price: float
    ts: datetime


class OHLCResponse(BaseModel):
    symbol: str
    timeframe: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
