from __future__ import annotations

from dataclasses import dataclass

from ..exchanges.base import BaseExchange
from ..exchanges.models import Order, OrderSide, OrderType
from ..services.signal_service import SignalService


@dataclass
class SignalBotConfig:
    symbol: str
    coin_id: str
    signal_type: str = "rsi_ema"
    buy_threshold: float = 0.0
    sell_threshold: float = 0.0
    amount: float = 0.0


class SignalBot:
    def __init__(self, *, exchange: BaseExchange, config: SignalBotConfig):
        self.exchange = exchange
        self.config = config

    async def tick(self, *, market_price: float) -> Order | None:
        """Check signal and place an order when BUY/SELL.

        Thresholds are reserved for future numeric signal scores; currently
        we act on discrete BUY/SELL from SignalService.
        """

        sig = await SignalService.get_signal(self.config.coin_id, symbol=self.config.symbol)

        if sig.signal == "BUY":
            return await self.exchange.place_order(
                symbol=self.config.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                amount=self.config.amount,
                price=market_price,
            )

        if sig.signal == "SELL":
            return await self.exchange.place_order(
                symbol=self.config.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=self.config.amount,
                price=market_price,
            )

        return None
