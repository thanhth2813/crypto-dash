from __future__ import annotations

from dataclasses import dataclass

from ..exchanges.base import BaseExchange
from ..exchanges.models import Order, OrderSide, OrderType
from ..services.signal_service import SignalService
from .dca_bot import _floor_to_step


@dataclass
class SignalBotConfig:
    symbol: str
    coin_id: str
    signal_type: str = "rsi_ema"
    buy_threshold: float = 0.0
    sell_threshold: float = 0.0
    amount: float = 0.0  # Quote currency (USDT) per trade
    amount_unit: str = "USDT"
    step_size: float = 0.00001
    min_notional: float = 10.0


class SignalBot:
    def __init__(self, *, exchange: BaseExchange, config: SignalBotConfig):
        self.exchange = exchange
        self.config = config

    async def tick(self, *, market_price: float) -> Order | None:
        """Check signal and place an order when BUY/SELL.

        Config amount is in quote currency (USDT).
        Converts to base qty with LOT_SIZE rounding + MIN_NOTIONAL check.
        """

        if market_price <= 0:
            return None

        sig = await SignalService.get_signal(self.config.coin_id, symbol=self.config.symbol)

        if sig.signal not in ("BUY", "SELL"):
            return None

        # Convert quote amount to base quantity
        base_qty = self.config.amount / market_price
        base_qty = _floor_to_step(base_qty, self.config.step_size)

        if base_qty <= 0:
            return None

        notional = base_qty * market_price
        if notional < self.config.min_notional:
            return None

        side = OrderSide.BUY if sig.signal == "BUY" else OrderSide.SELL

        return await self.exchange.place_order(
            symbol=self.config.symbol,
            side=side,
            order_type=OrderType.MARKET,
            amount=base_qty,
            price=market_price,
        )
