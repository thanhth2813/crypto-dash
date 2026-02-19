"""Trade history endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.trade import TradeResponse, TradeSummary
from ..services.trade_service import TradeService

router = APIRouter(prefix="/trades", tags=["trades"])


def _to_float(v) -> float:
    """Convert Decimal to float."""
    return float(v) if v is not None else 0.0


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    limit: int = Query(50, le=100, description="Max trades to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[TradeResponse]:
    """List user's trade history (paginated)."""
    trades, total = await TradeService.list_trades(db, user.id, bot_id, limit, offset)
    
    return [
        TradeResponse(
            id=trade.id,
            bot_id=trade.bot_id,
            bot_name=bot_name,
            exchange=trade.exchange,
            symbol=trade.symbol,
            side=trade.side,
            order_type=trade.order_type,
            amount=_to_float(trade.amount),
            price=_to_float(trade.price),
            filled_amount=_to_float(trade.filled_amount),
            filled_price=_to_float(trade.filled_price),
            status=trade.status,
            fee=_to_float(trade.fee),
            fee_currency=trade.fee_currency,
            created_at=trade.created_at,
            executed_at=trade.executed_at,
        )
        for trade, bot_name in trades
    ]


@router.get("/summary", response_model=TradeSummary)
async def get_summary(
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> TradeSummary:
    """Get trade history summary."""
    summary = await TradeService.get_summary(db, user.id, bot_id)
    return TradeSummary(**summary)
