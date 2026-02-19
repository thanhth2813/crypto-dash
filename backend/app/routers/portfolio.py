from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.portfolio import (
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
    HoldingWithPnlResponse,
    PortfolioSummary,
)
from ..services.market_service import MarketService
from ..services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _to_float(v) -> float:
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


@router.post("", response_model=HoldingResponse)
async def add_holding(
    req: HoldingCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> HoldingResponse:
    h = await PortfolioService.add_holding(db, user.id, req)
    return HoldingResponse(
        id=h.id,
        coin_id=h.coin_id,
        symbol=h.symbol,
        amount=_to_float(h.amount),
        buy_price=_to_float(h.buy_price),
    )


@router.get("", response_model=list[HoldingWithPnlResponse])
async def list_holdings(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[HoldingWithPnlResponse]:
    holdings = await PortfolioService.list_holdings(db, user.id)

    market = await MarketService.get_top_prices()
    price_by_coin: dict[str, float] = {}
    for item in market:
        cid = str(item.get("id"))
        cp = item.get("current_price")
        if cid and cp is not None:
            price_by_coin[cid] = float(cp)

    out: list[HoldingWithPnlResponse] = []
    for h in holdings:
        amount = _to_float(h.amount)
        buy_price = _to_float(h.buy_price)
        current_price = price_by_coin.get(h.coin_id, buy_price)
        pnl = (current_price - buy_price) * amount

        out.append(
            HoldingWithPnlResponse(
                id=h.id,
                coin_id=h.coin_id,
                symbol=h.symbol,
                amount=amount,
                buy_price=buy_price,
                current_price=current_price,
                pnl=pnl,
            )
        )

    return out


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: int,
    req: HoldingUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> HoldingResponse:
    h = await PortfolioService.update_holding(db, user.id, holding_id, req)
    return HoldingResponse(
        id=h.id,
        coin_id=h.coin_id,
        symbol=h.symbol,
        amount=_to_float(h.amount),
        buy_price=_to_float(h.buy_price),
    )


@router.delete("/{holding_id}")
async def delete_holding(
    holding_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    await PortfolioService.delete_holding(db, user.id, holding_id)
    return {"ok": True}


@router.get("/summary", response_model=PortfolioSummary)
async def summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> PortfolioSummary:
    data = await PortfolioService.get_summary(db, user.id)
    return PortfolioSummary(**data)
