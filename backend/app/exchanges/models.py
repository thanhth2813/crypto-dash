from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass
class Balance:
    asset: str
    free: float
    locked: float = 0.0


@dataclass
class Ticker:
    symbol: str
    price: float
    ts: float | None = None  # epoch seconds


@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    amount: float
    price: float | None = None
    filled_amount: float = 0.0
    avg_fill_price: float | None = None
    raw: dict[str, Any] | None = None
