"""Trade order model."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

import enum


class OrderSide(str, enum.Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, enum.Enum):
    """Order execution status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeOrder(Base):
    """Trade order execution record."""
    __tablename__ = "trade_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("trading_bots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    exchange: Mapped[str] = mapped_column(String, nullable=False)  # binance/paper
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)  # BTCUSDT
    side: Mapped[str] = mapped_column(String, nullable=False)  # buy/sell
    order_type: Mapped[str] = mapped_column(String, nullable=False)  # market/limit
    
    # Order details
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)  # NULL for market orders
    filled_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    filled_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Exchange's order ID
    
    # Fees
    fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    fee_currency: Mapped[str | None] = mapped_column(String, nullable=True)  # USDT/BTC/etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    bot = relationship("TradingBot", back_populates="orders")
    user = relationship("User", back_populates="trade_orders")
