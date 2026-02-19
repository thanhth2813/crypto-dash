from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.holding import Holding
from ..schemas.portfolio import HoldingCreate, HoldingUpdate
from ..services.market_service import MarketService


def _to_float(v) -> float:
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


class PortfolioService:
    @staticmethod
    async def add_holding(db: AsyncSession, user_id: int, req: HoldingCreate) -> Holding:
        holding = Holding(
            user_id=user_id,
            coin_id=req.coin_id,
            symbol=req.symbol,
            amount=req.amount,
            buy_price=req.buy_price,
        )
        db.add(holding)
        await db.commit()
        await db.refresh(holding)
        return holding

    @staticmethod
    async def list_holdings(db: AsyncSession, user_id: int) -> list[Holding]:
        res = await db.execute(select(Holding).where(Holding.user_id == user_id).order_by(Holding.id.desc()))
        return list(res.scalars().all())

    @staticmethod
    async def update_holding(db: AsyncSession, user_id: int, holding_id: int, req: HoldingUpdate) -> Holding:
        res = await db.execute(select(Holding).where(Holding.id == holding_id, Holding.user_id == user_id))
        holding = res.scalar_one_or_none()
        if holding is None:
            raise HTTPException(status_code=404, detail="holding not found")

        if req.amount is not None:
            holding.amount = req.amount
        if req.buy_price is not None:
            holding.buy_price = req.buy_price

        await db.commit()
        await db.refresh(holding)
        return holding

    @staticmethod
    async def delete_holding(db: AsyncSession, user_id: int, holding_id: int) -> None:
        res = await db.execute(select(Holding).where(Holding.id == holding_id, Holding.user_id == user_id))
        holding = res.scalar_one_or_none()
        if holding is None:
            raise HTTPException(status_code=404, detail="holding not found")

        await db.delete(holding)
        await db.commit()

    @staticmethod
    async def get_summary(db: AsyncSession, user_id: int) -> dict:
        holdings = await PortfolioService.list_holdings(db, user_id)

        market = await MarketService.get_top_prices()
        price_by_coin: dict[str, float] = {}
        for item in market:
            cid = str(item.get("id"))
            cp = item.get("current_price")
            if cid and cp is not None:
                price_by_coin[cid] = float(cp)

        total_invested = 0.0
        total_value = 0.0
        allocation_map: dict[tuple[str, str], float] = {}

        for h in holdings:
            amount = _to_float(h.amount)
            buy_price = _to_float(h.buy_price)
            invested = amount * buy_price
            total_invested += invested

            current_price = price_by_coin.get(h.coin_id, buy_price)
            value = amount * current_price
            total_value += value

            key = (h.coin_id, h.symbol)
            allocation_map[key] = allocation_map.get(key, 0.0) + value

        total_pnl = total_value - total_invested

        allocation = []
        for (coin_id, symbol), value in allocation_map.items():
            weight = (value / total_value) if total_value > 0 else 0.0
            allocation.append({"coin_id": coin_id, "symbol": symbol, "value": value, "weight": weight})

        allocation.sort(key=lambda x: x["value"], reverse=True)

        return {
            "total_invested": total_invested,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "allocation": allocation,
        }
