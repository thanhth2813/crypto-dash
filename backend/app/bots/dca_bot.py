from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..exchanges.base import BaseExchange
from ..exchanges.models import Order, OrderSide, OrderType


@dataclass
class DcaBotConfig:
    symbol: str
    amount_per_buy: float  # Quote currency (USDT) amount per buy
    interval_minutes: int
    max_buys: int
    amount_unit: str = "USDT"  # Always quote currency
    step_size: float = 0.00001  # LOT_SIZE filter (Binance default for BTC)
    min_notional: float = 10.0  # MIN_NOTIONAL filter (Binance: $10 minimum)


def _floor_to_step(qty: float, step: float) -> float:
    """Round down to exchange step size (LOT_SIZE filter)."""
    if step <= 0:
        return qty
    precision = max(0, -int(math.log10(step)))
    return round(math.floor(qty / step) * step, precision)


class DcaBot:
    def __init__(self, *, exchange: BaseExchange, config: DcaBotConfig):
        self.exchange = exchange
        self.config = config
        self._buys_done = 0

    @property
    def buys_done(self) -> int:
        return self._buys_done

    async def tick(self, *, market_price: float) -> Order | None:
        """Execute one DCA step if under max buys.

        Config amount_per_buy is in quote currency (USDT).
        Converts to base asset qty, applies LOT_SIZE rounding,
        and checks MIN_NOTIONAL before placing order.
        """

        if self._buys_done >= self.config.max_buys:
            return None

        if market_price <= 0:
            return None

        # Convert quote amount (USDT) to base asset quantity
        quote_amount = self.config.amount_per_buy
        base_qty = quote_amount / market_price

        # Apply LOT_SIZE step rounding
        base_qty = _floor_to_step(base_qty, self.config.step_size)

        if base_qty <= 0:
            return None

        # Check MIN_NOTIONAL (order value must exceed minimum)
        notional = base_qty * market_price
        if notional < self.config.min_notional:
            return None

        order = await self.exchange.place_order(
            symbol=self.config.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=base_qty,
            price=market_price,  # required for PaperExchange
        )

        self._buys_done += 1
        return order
