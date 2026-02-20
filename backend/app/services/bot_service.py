"""Bot service for CRUD operations."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.trade_order import TradeOrder
from ..models.trading_bot import TradingBot
from ..schemas.bot import BotCreate, BotUpdate


class BotService:
    """Trading bot management service."""
    
    @staticmethod
    async def create_bot(db: AsyncSession, user_id: int, req: BotCreate) -> TradingBot:
        """Create a new trading bot."""
        bot = TradingBot(
            user_id=user_id,
            name=req.name,
            strategy=req.strategy,
            exchange=req.exchange,
            symbol=req.symbol.upper(),
            config=req.config,
            risk_config={
                "max_position_usd": 100,
                "max_daily_loss_pct": 10,
                "max_consecutive_losses": 5,
                "max_drawdown_pct": 15,
            },
            paper_mode=req.paper_mode,
            status="created",
            total_invested=0,
            total_pnl=0,
        )
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        return bot
    
    @staticmethod
    async def list_bots(db: AsyncSession, user_id: int) -> list[TradingBot]:
        """List all user bots."""
        result = await db.execute(
            select(TradingBot)
            .where(TradingBot.user_id == user_id)
            .order_by(TradingBot.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_bot(db: AsyncSession, user_id: int, bot_id: int) -> TradingBot:
        """Get bot by ID (with ownership check)."""
        result = await db.execute(
            select(TradingBot)
            .where(TradingBot.id == bot_id, TradingBot.user_id == user_id)
        )
        bot = result.scalar_one_or_none()
        if not bot:
            raise HTTPException(status_code=404, detail="bot not found")
        return bot
    
    @staticmethod
    async def get_bot_with_orders(
        db: AsyncSession, user_id: int, bot_id: int, limit: int = 10
    ) -> tuple[TradingBot, list[TradeOrder]]:
        """Get bot with recent orders."""
        bot = await BotService.get_bot(db, user_id, bot_id)
        
        result = await db.execute(
            select(TradeOrder)
            .where(TradeOrder.bot_id == bot_id)
            .order_by(TradeOrder.created_at.desc())
            .limit(limit)
        )
        orders = list(result.scalars().all())
        
        return bot, orders
    
    @staticmethod
    async def update_bot(
        db: AsyncSession, user_id: int, bot_id: int, req: BotUpdate
    ) -> TradingBot:
        """Update bot configuration (only if stopped)."""
        bot = await BotService.get_bot(db, user_id, bot_id)
        
        if bot.status == "running":
            raise HTTPException(
                status_code=400, detail="cannot update running bot - stop it first"
            )
        
        if req.name is not None:
            bot.name = req.name
        if req.config is not None:
            bot.config = req.config
        
        await db.commit()
        await db.refresh(bot)
        return bot
    
    @staticmethod
    async def start_bot(db: AsyncSession, user_id: int, bot_id: int) -> TradingBot:
        """Start a bot (mark as running)."""
        bot = await BotService.get_bot(db, user_id, bot_id)
        
        if bot.status == "running":
            raise HTTPException(status_code=400, detail="bot already running")
        
        bot.status = "running"
        bot.started_at = datetime.now(timezone.utc)
        bot.stopped_at = None
        
        await db.commit()
        await db.refresh(bot)
        
        # Trigger BotManager to start the bot
        from ..bots.manager import BotManager
        manager = BotManager.get_instance()
        await manager.start_bot(bot.id)
        
        return bot
    
    @staticmethod
    async def stop_bot(db: AsyncSession, user_id: int, bot_id: int) -> TradingBot:
        """Stop a bot (mark as stopped)."""
        bot = await BotService.get_bot(db, user_id, bot_id)
        
        if bot.status != "running":
            raise HTTPException(status_code=400, detail="bot not running")
        
        bot.status = "stopped"
        bot.stopped_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(bot)
        
        # Trigger BotManager to stop the bot
        from ..bots.manager import BotManager
        manager = BotManager.get_instance()
        await manager.stop_bot(bot.id)
        
        return bot
    
    @staticmethod
    async def delete_bot(db: AsyncSession, user_id: int, bot_id: int) -> None:
        """Delete a bot (only if stopped)."""
        bot = await BotService.get_bot(db, user_id, bot_id)
        
        if bot.status == "running":
            raise HTTPException(
                status_code=400, detail="cannot delete running bot - stop it first"
            )
        
        await db.delete(bot)
        await db.commit()
