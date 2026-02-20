from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from .base import BaseExchange
from .models import Balance, Order, OrderSide, OrderStatus, OrderType, Ticker


class BinanceExchange(BaseExchange):
    """Binance Exchange connector (REST).

    Implements:
    - Public: ticker
    - Private (signed): account balance, orders (place/cancel/get/open)

    Notes:
    - Upper layer should handle encryption/decryption of api_key/api_secret.
    - This connector uses simple REST requests; it does not implement websocket streams.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = "https://api.binance.com",
        recv_window: int = 5000,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-MBX-APIKEY": self.api_key}

    def _sign_request(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_secret:
            raise ValueError("Missing Binance api_secret")

        query = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        signed: bool = False,
        weight: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        """HTTP request helper with minimal rate-limit awareness.

        - If signed=True, adds timestamp+recvWindow and HMAC signature.
        - Retries on 429/418 with small backoff.
        """

        url = f"{self.base_url}{path}"
        p: dict[str, Any] = dict(params or {})

        if signed:
            p.setdefault("timestamp", int(time.time() * 1000))
            p.setdefault("recvWindow", self.recv_window)
            p = self._sign_request(p)

        headers = self._headers()

        # Basic backoff loop for rate limiting
        for attempt in range(3):
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.request(method, url, params=p, headers=headers)

            # Rate limit / bans
            if resp.status_code in (418, 429):
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after and retry_after.isdigit() else (1.0 + attempt)
                await _sleep(sleep_s)
                continue

            # Parse JSON
            try:
                data = resp.json()
            except Exception:
                resp.raise_for_status()
                raise

            if resp.is_error:
                # Binance error format: {"code": -XXXX, "msg": "..."}
                raise BinanceApiError(code=int(data.get("code", 0)), msg=str(data.get("msg", "")), raw=data)

            return data

        raise BinanceApiError(code=-1, msg="rate limited", raw={"path": path})

    async def get_ticker(self, symbol: str) -> Ticker:
        data = await self._request("GET", "/api/v3/ticker/price", params={"symbol": symbol}, signed=False)
        return Ticker(symbol=symbol, price=float(data["price"]), ts=time.time())

    async def get_balance(self) -> dict[str, Balance]:
        try:
            data = await self._request("GET", "/api/v3/account", signed=True)
            balances = {}
            for b in data.get("balances", []) or []:
                asset = str(b.get("asset"))
                free = float(b.get("free", 0) or 0)
                locked = float(b.get("locked", 0) or 0)
                balances[asset] = Balance(asset=asset, free=free, locked=locked)
            return balances
        except BinanceApiError as exc:
            # Return empty dict on failure; caller may decide.
            raise exc

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
    ) -> Order:
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": _fmt_qty(amount),
        }

        if order_type == OrderType.LIMIT:
            if price is None:
                return _failed_order(symbol, side, order_type, amount, price, "LIMIT requires price")
            params["price"] = _fmt_price(price)
            params["timeInForce"] = "GTC"

        try:
            data = await self._request("POST", "/api/v3/order", params=params, signed=True)
            return _order_from_binance(data, symbol=symbol, side=side, order_type=order_type)
        except BinanceApiError as exc:
            return _failed_order(symbol, side, order_type, amount, price, exc.msg, raw=exc.raw)

    async def cancel_order(self, order_id: str) -> bool:
        # Binance requires symbol; in this interface we only have order_id.
        # Caller should use get_order/open_orders to retrieve symbol if needed.
        raise NotImplementedError("cancel_order requires symbol on Binance; use cancel_order_by_symbol")

    async def cancel_order_by_symbol(self, *, symbol: str, order_id: str) -> bool:
        try:
            await self._request(
                "DELETE",
                "/api/v3/order",
                params={"symbol": symbol, "orderId": order_id},
                signed=True,
            )
            return True
        except BinanceApiError:
            return False

    async def get_order(self, order_id: str) -> Order:
        raise NotImplementedError("get_order requires symbol on Binance; use get_order_by_symbol")

    async def get_order_by_symbol(self, *, symbol: str, order_id: str) -> Order:
        try:
            data = await self._request(
                "GET",
                "/api/v3/order",
                params={"symbol": symbol, "orderId": order_id},
                signed=True,
            )
            side = OrderSide(str(data.get("side", "BUY")))
            otype = OrderType(str(data.get("type", "MARKET")))
            return _order_from_binance(data, symbol=symbol, side=side, order_type=otype)
        except BinanceApiError as exc:
            return _failed_order(symbol, OrderSide.BUY, OrderType.MARKET, 0.0, None, exc.msg, raw=exc.raw)

    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol

        try:
            data = await self._request("GET", "/api/v3/openOrders", params=params, signed=True)
            out: list[Order] = []
            for row in data or []:
                sym = str(row.get("symbol", symbol or ""))
                side = OrderSide(str(row.get("side", "BUY")))
                otype = OrderType(str(row.get("type", "LIMIT")))
                out.append(_order_from_binance(row, symbol=sym, side=side, order_type=otype))
            return out
        except BinanceApiError:
            return []


class BinanceApiError(Exception):
    def __init__(self, *, code: int, msg: str, raw: dict[str, Any] | None = None):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.raw = raw or {}


def _fmt_qty(q: float) -> str:
    return format(float(q), "f").rstrip("0").rstrip(".") or "0"


def _fmt_price(p: float) -> str:
    return format(float(p), "f").rstrip("0").rstrip(".") or "0"


def _status_from_binance(s: str) -> OrderStatus:
    st = (s or "").upper()
    if st == "FILLED":
        return OrderStatus.FILLED
    if st in ("CANCELED", "CANCELLED", "EXPIRED", "REJECTED"):
        return OrderStatus.CANCELLED
    if st in ("NEW", "PARTIALLY_FILLED", "PENDING_CANCEL"):
        return OrderStatus.PENDING
    return OrderStatus.FAILED


def _order_from_binance(data: dict[str, Any], *, symbol: str, side: OrderSide, order_type: OrderType) -> Order:
    oid = str(data.get("orderId") or data.get("clientOrderId") or "")
    status = _status_from_binance(str(data.get("status", "")))

    qty = float(data.get("origQty") or data.get("quantity") or 0.0)
    executed = float(data.get("executedQty") or 0.0)

    price = data.get("price")
    price_f = float(price) if price not in (None, "") else None

    avg = data.get("cummulativeQuoteQty")
    avg_fill = None
    if executed and avg not in (None, ""):
        try:
            avg_fill = float(avg) / executed
        except Exception:
            avg_fill = None

    return Order(
        id=oid,
        symbol=symbol,
        side=side,
        order_type=order_type,
        status=status,
        amount=qty,
        price=price_f,
        filled_amount=executed,
        avg_fill_price=avg_fill,
        raw=data,
    )


def _failed_order(
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    amount: float,
    price: float | None,
    msg: str,
    raw: dict[str, Any] | None = None,
) -> Order:
    return Order(
        id="",
        symbol=symbol,
        side=side,
        order_type=order_type,
        status=OrderStatus.FAILED,
        amount=float(amount),
        price=price,
        filled_amount=0.0,
        avg_fill_price=None,
        raw={"message": msg, **(raw or {})},
    )


async def _sleep(seconds: float) -> None:
    # small wrapper to avoid importing asyncio at module import time in some contexts
    import asyncio

    await asyncio.sleep(seconds)
