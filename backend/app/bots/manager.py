"""Bot Manager - Singleton service for managing running bots."""
from __future__ import annotations

import logging
from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..database import SessionLocal

logger = logging.getLogger(__name__)


class BotManager:
    """Singleton manager for bot lifecycle."""
    
    _instance: BotManager | None = None
    
    def __init__(self):
        if BotManager._instance is not None:
            raise RuntimeError("BotManager is a singleton. Use BotManager.get_instance()")
        
        self.scheduler = AsyncIOScheduler()
        self.running_bots: Dict[int, dict] = {}  # bot_id -> {job_id, config, ...}
        self.scheduler.start()
        logger.info("BotManager initialized with APScheduler")
    
    @classmethod
    def get_instance(cls) -> BotManager:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = BotManager()
        return cls._instance
    
    async def start_bot(self, bot_id: int) -> None:
        """Start a bot (schedule its strategy execution)."""
        if bot_id in self.running_bots:
            logger.warning(f"Bot {bot_id} already running")
            return
        
        async with SessionLocal() as db:
            # Fetch bot config
            result = await db.execute(
                """SELECT id, user_id, strategy, symbol, config, paper_mode 
                   FROM trading_bots WHERE id = :bot_id"""
            )
            bot_row = result.fetchone()
            
            if not bot_row:
                logger.error(f"Bot {bot_id} not found")
                return
            
            bot_data = {
                "id": bot_row[0],
                "user_id": bot_row[1],
                "strategy": bot_row[2],
                "symbol": bot_row[3],
                "config": bot_row[4],
                "paper_mode": bot_row[5],
            }
        
        # Schedule based on strategy
        strategy = bot_data["strategy"]
        interval_seconds = bot_data["config"].get("interval_seconds", 60)
        
        job_id = f"bot_{bot_id}"
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self._execute_bot_tick,
            trigger="interval",
            seconds=interval_seconds,
            id=job_id,
            args=[bot_id, bot_data],
            replace_existing=True,
        )
        
        self.running_bots[bot_id] = {
            "job_id": job_id,
            "strategy": strategy,
            "symbol": bot_data["symbol"],
        }
        
        logger.info(f"Bot {bot_id} started ({strategy}, interval={interval_seconds}s)")
    
    async def stop_bot(self, bot_id: int) -> None:
        """Stop a bot (cancel scheduled tasks)."""
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} not running")
            return
        
        job_id = self.running_bots[bot_id]["job_id"]
        
        # Remove job from scheduler
        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
        
        del self.running_bots[bot_id]
        logger.info(f"Bot {bot_id} stopped")
    
    async def _execute_bot_tick(self, bot_id: int, bot_data: dict) -> None:
        """Execute one tick of bot logic."""
        strategy = bot_data["strategy"]
        
        try:
            if strategy == "dca":
                await self._run_dca_tick(bot_id, bot_data)
            elif strategy == "grid":
                await self._run_grid_tick(bot_id, bot_data)
            elif strategy == "signal":
                await self._run_signal_tick(bot_id, bot_data)
            else:
                logger.error(f"Unknown strategy: {strategy}")
        except Exception as e:
            logger.error(f"Bot {bot_id} tick failed: {e}", exc_info=True)
            
            # Mark bot as error status
            async with SessionLocal() as db:
                await db.execute(
                    """UPDATE trading_bots SET status = 'error' WHERE id = :bot_id""",
                    {"bot_id": bot_id}
                )
                await db.commit()
            
            # Stop the bot
            await self.stop_bot(bot_id)
    
    async def _run_dca_tick(self, bot_id: int, bot_data: dict) -> None:
        """Run DCA strategy tick."""
        # TODO: Implement DCA logic
        #  - Get current price
        #  - Check if it's time to buy (based on interval)
        #  - Place buy order
        #  - Update bot P&L
        logger.debug(f"DCA tick for bot {bot_id}")
    
    async def _run_grid_tick(self, bot_id: int, bot_data: dict) -> None:
        """Run Grid strategy tick."""
        # TODO: Implement Grid logic
        #  - Get current price
        #  - Check grid levels
        #  - Place buy/sell orders at grid levels
        #  - Update bot P&L
        logger.debug(f"Grid tick for bot {bot_id}")
    
    async def _run_signal_tick(self, bot_id: int, bot_data: dict) -> None:
        """Run Signal-based strategy tick."""
        # TODO: Implement Signal logic
        #  - Get current signals (RSI, EMA, etc.)
        #  - Evaluate trading conditions
        #  - Place orders based on signals
        #  - Update bot P&L
        logger.debug(f"Signal tick for bot {bot_id}")
    
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("BotManager shutdown")
