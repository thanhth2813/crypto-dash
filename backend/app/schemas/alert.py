from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertCreate(BaseModel):
    symbol: str
    coin_id: str
    condition: str  # 'above' | 'below'
    target_price: float


class AlertResponse(BaseModel):
    id: int
    symbol: str
    coin_id: str
    condition: str
    target_price: float
    status: str
    trigger_count: int
    triggered_at: datetime | None = None
