from __future__ import annotations

import bisect
from dataclasses import dataclass

from ..exchanges.base import BaseExchange
from ..exchanges.models import Order, OrderSide, OrderType


@dataclass
class GridBotConfig:
    symbol: str
    upper_price: float
    lower_price: float
    grid_count: int
    amount_per_grid: float


class GridBot:
    """Simple grid bot.

    - Divides [lower_price, upper_price] into N levels.
    - Places BUY limits below current price, SELL limits above.

    For paper mode: limit fills can be simulated by calling `tick(current_price)` and
    checking if current price crossed any order level.

    NOTE: This is an MVP skeleton; live order tracking requires exchange order ids
    and persistence.
    """

    def __init__(self, *, exchange: BaseExchange, config: GridBotConfig):
        self.exchange = exchange
        self.config = config
        self.levels: list[float] = []
        self.open_orders: dict[float, Order] = {}  # level -> order
        self.initialized = False

    def _build_levels(self) -> list[float]:
        if self.config.grid_count <= 0:
            return []
        step = (self.config.upper_price - self.config.lower_price) / self.config.grid_count
        return [self.config.lower_price + step * i for i in range(self.config.grid_count + 1)]

    async def initialize(self, *, current_price: float) -> list[Order]:
        self.levels = self._build_levels()
        self.open_orders = {}
        self.initialized = True

        orders: list[Order] = []
        for lvl in self.levels:
            if lvl < current_price:
                o = await self.exchange.place_order(
                    symbol=self.config.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    amount=self.config.amount_per_grid,
                    price=lvl,
                )
                self.open_orders[lvl] = o
                orders.append(o)
            elif lvl > current_price:
                o = await self.exchange.place_order(
                    symbol=self.config.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    amount=self.config.amount_per_grid,
                    price=lvl,
                )
                self.open_orders[lvl] = o
                orders.append(o)

        return orders

    async def tick(self, *, current_price: float) -> list[Order]:
        """For paper mode: simulate fills when price crosses limit levels.

        Returns newly placed opposite orders.
        """

        if not self.initialized:
            return await self.initialize(current_price=current_price)

        # Find crossed levels and rotate grid
        new_orders: list[Order] = []

        # BUY fills: if price <= buy level
        buy_levels = [lvl for lvl, o in self.open_orders.items() if o.side == OrderSide.BUY]
        for lvl in buy_levels:
            if current_price <= lvl:
                # filled -> place sell at next level above
                idx = bisect.bisect_right(self.levels, lvl)
                if idx < len(self.levels):
                    sell_lvl = self.levels[idx]
                    o = await self.exchange.place_order(
                        symbol=self.config.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.LIMIT,
                        amount=self.config.amount_per_grid,
                        price=sell_lvl,
                    )
                    self.open_orders[sell_lvl] = o
                    new_orders.append(o)
                self.open_orders.pop(lvl, None)

        # SELL fills: if price >= sell level
        sell_levels = [lvl for lvl, o in self.open_orders.items() if o.side == OrderSide.SELL]
        for lvl in sell_levels:
            if current_price >= lvl:
                # filled -> place buy at next level below
                idx = bisect.bisect_left(self.levels, lvl) - 1
                if idx >= 0:
                    buy_lvl = self.levels[idx]
                    o = await self.exchange.place_order(
                        symbol=self.config.symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.LIMIT,
                        amount=self.config.amount_per_grid,
                        price=buy_lvl,
                    )
                    self.open_orders[buy_lvl] = o
                    new_orders.append(o)
                self.open_orders.pop(lvl, None)

        return new_orders
