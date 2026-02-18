from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)

    symbol: Mapped[str] = mapped_column(String, index=True, nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[str] = mapped_column(String, default="active", nullable=False)  # active|triggered|paused
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
