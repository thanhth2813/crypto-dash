from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Balance, Order, OrderSide, OrderType, Ticker


class BaseExchange(ABC):
    @abstractmethod
    async def get_balance(self) -> dict[str, Balance]:
        raise NotImplementedError

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        raise NotImplementedError

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
    ) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        raise NotImplementedError
