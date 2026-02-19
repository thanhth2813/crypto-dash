from __future__ import annotations

from dataclasses import dataclass

from ..exchanges.base import BaseExchange
from ..exchanges.models import Order, OrderSide, OrderType


@dataclass
class DcaBotConfig:
    symbol: str
    amount_per_buy: float
    interval_minutes: int
    max_buys: int


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

        Caller is responsible for scheduling tick() every interval.
        """

        if self._buys_done >= self.config.max_buys:
            return None

        order = await self.exchange.place_order(
            symbol=self.config.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=self.config.amount_per_buy,
            price=market_price,  # required for PaperExchange
        )

        self._buys_done += 1
        return order
