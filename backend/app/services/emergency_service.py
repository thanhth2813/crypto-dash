"""Emergency service - system-wide bot controls and health monitoring."""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select

from ..bots.manager import BotManager
from ..database import SessionLocal
from ..models.trading_bot import TradingBot

logger = logging.getLogger(__name__)


class EmergencyService:
    """Emergency controls for trading system."""

    @staticmethod
    async def stop_all_bots(reason: str = "Emergency stop") -> dict:
        """Stop ALL running bots immediately.
        
        Must work even if individual bots have errors.
        Returns summary of stopped bots and any failures.
        """
        manager = BotManager.get_instance()
        
        results = {
            "stopped": [],
            "failed": [],
            "total": 0,
        }
        
        async with SessionLocal() as db:
            # Get all running bots
            result = await db.execute(
                select(TradingBot).where(TradingBot.status == "running")
            )
            running_bots = result.scalars().all()
            results["total"] = len(running_bots)
            
            # Stop each bot
            for bot in running_bots:
                try:
                    # Stop via BotManager (cancels scheduler job)
                    await manager.stop_bot(bot.id)
                    
                    # Update DB status
                    bot.status = "stopped"
                    bot.stopped_at = datetime.utcnow()
                    
                    results["stopped"].append({
                        "id": bot.id,
                        "name": bot.name,
                        "strategy": bot.strategy,
                    })
                    
                    logger.info(f"Emergency stop: Bot {bot.id} ({bot.name}) - {reason}")
                    
                except Exception as e:
                    results["failed"].append({
                        "id": bot.id,
                        "name": bot.name,
                        "error": str(e),
                    })
                    logger.error(f"Failed to stop bot {bot.id}: {e}", exc_info=True)
            
            await db.commit()
        
        return results

    @staticmethod
    async def force_stop_bot(bot_id: int, reason: str = "Force stop") -> dict:
        """Force stop a specific bot.
        
        Returns status of the stop operation.
        """
        manager = BotManager.get_instance()
        
        async with SessionLocal() as db:
            result = await db.execute(
                select(TradingBot).where(TradingBot.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                return {"success": False, "error": "Bot not found"}
            
            try:
                # Stop via BotManager
                await manager.stop_bot(bot_id)
                
                # Update DB
                bot.status = "stopped"
                bot.stopped_at = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Force stop: Bot {bot_id} ({bot.name}) - {reason}")
                
                return {
                    "success": True,
                    "bot_id": bot_id,
                    "name": bot.name,
                    "reason": reason,
                }
                
            except Exception as e:
                logger.error(f"Failed to force stop bot {bot_id}: {e}", exc_info=True)
                return {"success": False, "error": str(e)}

    @staticmethod
    async def get_system_status() -> dict:
        """Get system health: running bots, total exposure, circuit breakers.
        
        Returns comprehensive system status.
        """
        manager = BotManager.get_instance()
        
        async with SessionLocal() as db:
            # Count running bots
            result = await db.execute(
                select(TradingBot).where(TradingBot.status == "running")
            )
            running_bots = result.scalars().all()
            
            # Calculate total exposure (sum of invested amounts)
            total_exposure = sum(bot.total_invested for bot in running_bots)
            
            # Count error bots
            result = await db.execute(
                select(TradingBot).where(TradingBot.status == "error")
            )
            error_bots = result.scalars().all()
            
            # Count all bots by status
            result = await db.execute(select(TradingBot))
            all_bots = result.scalars().all()
            
            status_counts = {}
            for bot in all_bots:
                status_counts[bot.status] = status_counts.get(bot.status, 0) + 1
        
        return {
            "running_bots": len(running_bots),
            "error_bots": len(error_bots),
            "total_exposure": float(total_exposure),
            "scheduler_active": len(manager.running_bots) > 0,
            "status_breakdown": status_counts,
            "circuit_breakers": {
                # Placeholder for future circuit breaker logic
                "max_exposure_triggered": False,
                "error_rate_triggered": False,
            },
            "running_bot_details": [
                {
                    "id": bot.id,
                    "name": bot.name,
                    "strategy": bot.strategy,
                    "symbol": bot.symbol,
                    "invested": float(bot.total_invested),
                    "pnl": float(bot.total_pnl),
                }
                for bot in running_bots
            ],
        }
