"""Bot management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.bot import BotCreate, BotDetailResponse, BotResponse, BotUpdate, TradeOrderResponse
from ..services.bot_service import BotService

router = APIRouter(prefix="/bots", tags=["bots"])


def _to_float(v) -> float:
    """Convert Decimal to float."""
    return float(v) if v is not None else 0.0


@router.post("", response_model=BotResponse)
async def create_bot(
    req: BotCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> BotResponse:
    """Create a new trading bot."""
    bot = await BotService.create_bot(db, user.id, req)
    return BotResponse(
        id=bot.id,
        user_id=bot.user_id,
        name=bot.name,
        strategy=bot.strategy,
        exchange=bot.exchange,
        symbol=bot.symbol,
        config=bot.config,
        status=bot.status,
        paper_mode=bot.paper_mode,
        total_invested=_to_float(bot.total_invested),
        total_pnl=_to_float(bot.total_pnl),
        created_at=bot.created_at,
        started_at=bot.started_at,
        stopped_at=bot.stopped_at,
    )


@router.get("", response_model=list[BotResponse])
async def list_bots(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[BotResponse]:
    """List all user's bots."""
    bots = await BotService.list_bots(db, user.id)
    return [
        BotResponse(
            id=bot.id,
            user_id=bot.user_id,
            name=bot.name,
            strategy=bot.strategy,
            exchange=bot.exchange,
            symbol=bot.symbol,
            config=bot.config,
            status=bot.status,
            paper_mode=bot.paper_mode,
            total_invested=_to_float(bot.total_invested),
            total_pnl=_to_float(bot.total_pnl),
            created_at=bot.created_at,
            started_at=bot.started_at,
            stopped_at=bot.stopped_at,
        )
        for bot in bots
    ]


@router.get("/{bot_id}", response_model=BotDetailResponse)
async def get_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> BotDetailResponse:
    """Get bot detail with recent orders."""
    bot, orders = await BotService.get_bot_with_orders(db, user.id, bot_id, limit=10)
    
    return BotDetailResponse(
        id=bot.id,
        user_id=bot.user_id,
        name=bot.name,
        strategy=bot.strategy,
        exchange=bot.exchange,
        symbol=bot.symbol,
        config=bot.config,
        status=bot.status,
        paper_mode=bot.paper_mode,
        total_invested=_to_float(bot.total_invested),
        total_pnl=_to_float(bot.total_pnl),
        created_at=bot.created_at,
        started_at=bot.started_at,
        stopped_at=bot.stopped_at,
        recent_orders=[
            TradeOrderResponse(
                id=order.id,
                bot_id=order.bot_id,
                exchange=order.exchange,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                amount=_to_float(order.amount),
                price=_to_float(order.price),
                filled_amount=_to_float(order.filled_amount),
                filled_price=_to_float(order.filled_price),
                status=order.status,
                exchange_order_id=order.exchange_order_id,
                fee=_to_float(order.fee),
                fee_currency=order.fee_currency,
                created_at=order.created_at,
                executed_at=order.executed_at,
            )
            for order in orders
        ],
    )


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> BotResponse:
    """Start a bot."""
    bot = await BotService.start_bot(db, user.id, bot_id)
    return BotResponse(
        id=bot.id,
        user_id=bot.user_id,
        name=bot.name,
        strategy=bot.strategy,
        exchange=bot.exchange,
        symbol=bot.symbol,
        config=bot.config,
        status=bot.status,
        paper_mode=bot.paper_mode,
        total_invested=_to_float(bot.total_invested),
        total_pnl=_to_float(bot.total_pnl),
        created_at=bot.created_at,
        started_at=bot.started_at,
        stopped_at=bot.stopped_at,
    )


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> BotResponse:
    """Stop a bot."""
    bot = await BotService.stop_bot(db, user.id, bot_id)
    return BotResponse(
        id=bot.id,
        user_id=bot.user_id,
        name=bot.name,
        strategy=bot.strategy,
        exchange=bot.exchange,
        symbol=bot.symbol,
        config=bot.config,
        status=bot.status,
        paper_mode=bot.paper_mode,
        total_invested=_to_float(bot.total_invested),
        total_pnl=_to_float(bot.total_pnl),
        created_at=bot.created_at,
        started_at=bot.started_at,
        stopped_at=bot.stopped_at,
    )


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    """Delete a bot (only if stopped)."""
    await BotService.delete_bot(db, user.id, bot_id)
    return {"ok": True}
