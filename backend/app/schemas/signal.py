from __future__ import annotations

from pydantic import BaseModel


class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float | None = None
