"""Background worker for scheduled jobs and bot execution."""
from __future__ import annotations

import asyncio
import logging
import signal

from ..bots.manager import BotManager

logger = logging.getLogger(__name__)


async def main():
    """Worker main loop with BotManager."""
    logger.info("Worker starting with BotManager...")
    
    # Initialize BotManager singleton
    manager = BotManager.get_instance()
    logger.info("BotManager initialized - APScheduler running")
    
    # Auto-load running bots from database
    from sqlalchemy import select
    from ..database import SessionLocal
    from ..models.trading_bot import TradingBot
    
    async with SessionLocal() as db:
        result = await db.execute(
            select(TradingBot).where(TradingBot.status == "running")
        )
        running_bots = result.scalars().all()
        
        if running_bots:
            logger.info(f"Auto-loading {len(running_bots)} running bots...")
            for bot in running_bots:
                try:
                    await manager.start_bot(bot.id)
                    logger.info(f"Loaded bot {bot.id}: {bot.name} ({bot.strategy})")
                except Exception as e:
                    logger.error(f"Failed to load bot {bot.id}: {e}")
        else:
            logger.info("No running bots found in database")
    
    # Setup graceful shutdown
    def shutdown_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        manager.shutdown()
        asyncio.get_event_loop().stop()
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Keep worker alive - scheduler runs in background
    try:
        while True:
            await asyncio.sleep(60)
            logger.debug(f"Worker heartbeat - {len(manager.running_bots)} bots running")
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    finally:
        manager.shutdown()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
