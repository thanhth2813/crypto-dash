from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Re-export models for Alembic discovery
from .user import User  # noqa: E402,F401
from .holding import Holding  # noqa: E402,F401
from .alert import Alert  # noqa: E402,F401
from .price_history import PriceHistory  # noqa: E402,F401
