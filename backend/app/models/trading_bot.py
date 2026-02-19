"""Trading bot model."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class BotStrategy(str, enum.Enum):
    """Bot trading strategies."""
    DCA = "dca"
    GRID = "grid"
    SIGNAL = "signal"


class BotStatus(str, enum.Enum):
    """Bot lifecycle status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TradingBot(Base):
    """Trading bot configuration and state."""
    __tablename__ = "trading_bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    strategy: Mapped[str] = mapped_column(String, nullable=False)  # dca/grid/signal
    exchange: Mapped[str] = mapped_column(String, nullable=False, default="paper")  # binance/paper
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)  # BTCUSDT
    
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Strategy-specific config
    status: Mapped[str] = mapped_column(String, nullable=False, default="created", index=True)
    paper_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # P&L tracking
    total_invested: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    total_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bots")
    orders = relationship("TradeOrder", back_populates="bot", cascade="all, delete-orphan")
