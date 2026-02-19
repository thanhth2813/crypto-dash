"""Background worker for scheduled jobs.

Placeholder until Codex implements Task #14 (APScheduler alert checker).
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def main():
    """Worker main loop (placeholder)."""
    logger.info("Worker started (placeholder - waiting for Task #14 implementation)")
    
    # Keep worker alive
    while True:
        await asyncio.sleep(60)
        logger.debug("Worker heartbeat")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
