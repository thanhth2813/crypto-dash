from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    coin_id: Mapped[str] = mapped_column(String, index=True, nullable=False)  # e.g. 'bitcoin'
    symbol: Mapped[str] = mapped_column(String, index=True, nullable=False)

    amount: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    buy_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)

    bought_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
