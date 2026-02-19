from __future__ import annotations

import time

import httpx

from .base import BaseExchange
from .models import Balance, Order, OrderSide, OrderType, Ticker


class BinanceExchange(BaseExchange):
    """Minimal Binance implementation.

    NOTE: This is a skeleton. For live trading, Binance requires signed requests.
    Here we implement public ticker via REST and leave private endpoints as TODO.

    Credentials should come from user config (encrypted in DB) and be decrypted
    by higher layers before instantiating this client.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, base_url: str = "https://api.binance.com"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

    async def get_balance(self) -> dict[str, Balance]:
        # TODO: implement signed endpoint GET /api/v3/account
        raise NotImplementedError("Binance private endpoints not implemented yet")

    async def get_ticker(self, symbol: str) -> Ticker:
        url = f"{self.base_url}/api/v3/ticker/price"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params={"symbol": symbol})
            resp.raise_for_status()
            data = resp.json()
        return Ticker(symbol=symbol, price=float(data["price"]), ts=time.time())

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
    ) -> Order:
        # TODO: implement signed endpoint POST /api/v3/order
        raise NotImplementedError("Binance private endpoints not implemented yet")

    async def cancel_order(self, order_id: str) -> bool:
        # TODO: implement signed endpoint DELETE /api/v3/order
        raise NotImplementedError("Binance private endpoints not implemented yet")

    async def get_order(self, order_id: str) -> Order:
        # TODO: implement signed endpoint GET /api/v3/order
        raise NotImplementedError("Binance private endpoints not implemented yet")

    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        # TODO: implement signed endpoint GET /api/v3/openOrders
        raise NotImplementedError("Binance private endpoints not implemented yet")
