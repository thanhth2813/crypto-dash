"""Trade history service."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.trade_order import TradeOrder
from ..models.trading_bot import TradingBot


class TradeService:
    """Trade history management service."""
    
    @staticmethod
    async def list_trades(
        db: AsyncSession,
        user_id: int,
        bot_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[TradeOrder, str]], int]:
        """List user trades with pagination."""
        # Base query with bot name join
        query = (
            select(TradeOrder, TradingBot.name)
            .join(TradingBot, TradeOrder.bot_id == TradingBot.id)
            .where(TradeOrder.user_id == user_id)
        )
        
        # Filter by bot_id if provided
        if bot_id is not None:
            query = query.where(TradeOrder.bot_id == bot_id)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(TradeOrder.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        trades = result.all()
        
        return trades, total
    
    @staticmethod
    async def get_summary(db: AsyncSession, user_id: int, bot_id: int | None = None) -> dict:
        """Get trade history summary."""
        # Base query
        query = select(TradeOrder).where(TradeOrder.user_id == user_id)
        
        if bot_id is not None:
            query = query.where(TradeOrder.bot_id == bot_id)
        
        result = await db.execute(query)
        trades = list(result.scalars().all())
        
        if not trades:
            return {
                "total_trades": 0,
                "total_buy": 0,
                "total_sell": 0,
                "total_volume": 0.0,
                "total_fees": 0.0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
            }
        
        total_trades = len(trades)
        total_buy = sum(1 for t in trades if t.side == "buy")
        total_sell = sum(1 for t in trades if t.side == "sell")
        
        total_volume = sum(float(t.filled_amount or 0) for t in trades)
        total_fees = sum(float(t.fee or 0) for t in trades)
        
        # Simplified P&L calculation (buy-sell pairs)
        # TODO: Implement proper P&L tracking per bot
        buy_volume = sum(
            float(t.filled_amount or 0) * float(t.filled_price or 0)
            for t in trades if t.side == "buy" and t.status == "filled"
        )
        sell_volume = sum(
            float(t.filled_amount or 0) * float(t.filled_price or 0)
            for t in trades if t.side == "sell" and t.status == "filled"
        )
        total_pnl = sell_volume - buy_volume - total_fees
        
        # Win rate (simplified: trades with positive P&L)
        # TODO: Implement per-trade P&L tracking
        win_rate = 0.5  # Placeholder
        
        return {
            "total_trades": total_trades,
            "total_buy": total_buy,
            "total_sell": total_sell,
            "total_volume": total_volume,
            "total_fees": total_fees,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
        }
