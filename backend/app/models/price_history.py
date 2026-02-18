from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    symbol: Mapped[str] = mapped_column(String, index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String, index=True, nullable=False)  # e.g. 1m|5m|1h|1d

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
