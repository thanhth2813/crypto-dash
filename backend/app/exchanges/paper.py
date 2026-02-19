from __future__ import annotations

import json
import random
from dataclasses import asdict
from uuid import uuid4

from ..utils.redis import get_redis_client
from .base import BaseExchange
from .models import Balance, Order, OrderSide, OrderStatus, OrderType, Ticker


class PaperExchange(BaseExchange):
    """Paper trading exchange.

    - Stores virtual balances in-memory and (optionally) Redis for persistence.
    - Fills market orders at ticker price with random slippage 0-0.1%.

    This is intentionally simple; production version should use atomic Redis ops.
    """

    def __init__(self, *, namespace: str = "paper", initial_balances: dict[str, float] | None = None):
        self.namespace = namespace
        self._balances: dict[str, Balance] = {}
        if initial_balances:
            for asset, free in initial_balances.items():
                self._balances[asset] = Balance(asset=asset, free=float(free), locked=0.0)

    def _balances_key(self) -> str:
        return f"paper:balances:{self.namespace}"

    async def _load_balances(self) -> None:
        try:
            r = get_redis_client()
            raw = await r.get(self._balances_key())
            if not raw:
                return
            data = json.loads(raw)
            self._balances = {k: Balance(**v) for k, v in data.items()}
        except Exception:
            return

    async def _save_balances(self) -> None:
        try:
            r = get_redis_client()
            payload = {k: asdict(v) for k, v in self._balances.items()}
            await r.set(self._balances_key(), json.dumps(payload))
        except Exception:
            return

    async def get_balance(self) -> dict[str, Balance]:
        await self._load_balances()
        return dict(self._balances)

    async def get_ticker(self, symbol: str) -> Ticker:
        # For paper, ticker should be provided by caller via MarketService;
        # here we only return placeholder.
        raise NotImplementedError("PaperExchange.get_ticker requires external price feed")

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
    ) -> Order:
        await self._load_balances()

        if order_type != OrderType.MARKET:
            return Order(
                id=str(uuid4()),
                symbol=symbol,
                side=side,
                order_type=order_type,
                status=OrderStatus.FAILED,
                amount=float(amount),
                price=price,
                raw={"error": "only MARKET supported"},
            )

        if price is None:
            return Order(
                id=str(uuid4()),
                symbol=symbol,
                side=side,
                order_type=order_type,
                status=OrderStatus.FAILED,
                amount=float(amount),
                raw={"error": "market price required"},
            )

        slip = random.uniform(0.0, 0.001)
        fill_price = float(price) * (1.0 + slip if side == OrderSide.BUY else 1.0 - slip)

        # Very simplified balance model: assume quote asset is USDT
        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"

        self._balances.setdefault(base_asset, Balance(asset=base_asset, free=0.0))
        self._balances.setdefault(quote_asset, Balance(asset=quote_asset, free=0.0))

        if side == OrderSide.BUY:
            cost = float(amount) * fill_price
            if self._balances[quote_asset].free < cost:
                status = OrderStatus.FAILED
            else:
                self._balances[quote_asset].free -= cost
                self._balances[base_asset].free += float(amount)
                status = OrderStatus.FILLED
        else:
            if self._balances[base_asset].free < float(amount):
                status = OrderStatus.FAILED
            else:
                proceeds = float(amount) * fill_price
                self._balances[base_asset].free -= float(amount)
                self._balances[quote_asset].free += proceeds
                status = OrderStatus.FILLED

        order = Order(
            id=str(uuid4()),
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            amount=float(amount),
            price=fill_price,
            filled_amount=float(amount) if status == OrderStatus.FILLED else 0.0,
            avg_fill_price=fill_price if status == OrderStatus.FILLED else None,
            raw={"slippage": slip},
        )

        await self._save_balances()
        return order

    async def cancel_order(self, order_id: str) -> bool:
        return True

    async def get_order(self, order_id: str) -> Order:
        # No order book in this simple implementation
        raise NotImplementedError

    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        return []
