"""Bot Manager - Singleton service for managing running bots."""
from __future__ import annotations

import logging
from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from ..database import SessionLocal
from ..models.trade_order import TradeOrder
from ..models.trading_bot import TradingBot

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
            # Fetch bot config using ORM
            result = await db.execute(
                select(TradingBot).where(TradingBot.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                logger.error(f"Bot {bot_id} not found")
                return
            
            bot_data = {
                "id": bot.id,
                "user_id": bot.user_id,
                "strategy": bot.strategy,
                "symbol": bot.symbol,
                "config": bot.config,
                "paper_mode": bot.paper_mode,
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

        # Risk check before placing any order (best-effort estimate)
        try:
            from ..services.risk_manager import RiskManager

            rm = RiskManager()
            cfg = bot_data.get("config") or {}

            # Estimate order amount in USD (quote)
            order_amount_usd = float(cfg.get("amount_per_buy") or cfg.get("amount") or 0.0)
            allowed, reason = await rm.check_order(
                bot_id=bot_id,
                user_id=bot_data.get("user_id"),
                order_amount_usd=order_amount_usd,
                symbol=bot_data.get("symbol"),
            )
            if not allowed:
                logger.warning(f"Bot {bot_id} blocked by RiskManager: {reason}")
                return
        except Exception as e:
            logger.warning(f"RiskManager check failed (fail-open): {e}")

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
                result = await db.execute(
                    select(TradingBot).where(TradingBot.id == bot_id)
                )
                bot = result.scalar_one_or_none()
                if bot:
                    bot.status = "error"
                    await db.commit()
            
            # Stop the bot
            await self.stop_bot(bot_id)
    
    async def _run_dca_tick(self, bot_id: int, bot_data: dict) -> None:
        """Run DCA strategy tick."""
        from ..exchanges.paper import PaperExchange
        from ..services.market_service import MarketService
        from .dca_bot import DcaBot, DcaBotConfig
        
        config = bot_data["config"]
        
        # Create exchange instance
        exchange = PaperExchange(
            namespace=f"bot_{bot_id}",
            initial_balances={"USDT": config.get("budget", 10000)}
        )
        
        # Get current market price
        prices = await MarketService.get_top_prices()
        symbol = bot_data["symbol"]
        # Extract coin_id from symbol (e.g., BTCUSDT -> bitcoin)
        coin_symbol = symbol.replace("USDT", "").lower()
        # Map common symbols to coin IDs
        coin_map = {"btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin"}
        coin_id = coin_map.get(coin_symbol, coin_symbol)
        
        market_price = next(
            (p["current_price"] for p in prices if p["id"] == coin_id),
            None
        )
        if not market_price:
            logger.warning(f"Bot {bot_id}: price not found for {coin_id}")
            return
        
        logger.info(f"Bot {bot_id}: DCA tick - symbol={symbol}, coin_id={coin_id}, price=${market_price}")
        
        # Create bot instance with valid config fields
        bot_config = DcaBotConfig(
            symbol=symbol,
            amount_per_buy=config.get("amount_per_buy", 0.001),
            interval_minutes=config.get("interval_minutes", 60),
            max_buys=config.get("max_buys", 10),
        )
        bot = DcaBot(exchange=exchange, config=bot_config)
        
        # Execute tick
        order = await bot.tick(market_price=market_price)
        
        logger.info(f"Bot {bot_id}: DCA tick result - order={order}, status={order.status.value if order else 'None'}")
        
        # Log order to database if filled
        if order and order.status.value == "FILLED":
            async with SessionLocal() as db:
                trade = TradeOrder(
                    bot_id=bot_id,
                    user_id=bot_data["user_id"],
                    exchange="paper",
                    symbol=symbol,
                    side=order.side.value,
                    order_type=order.order_type.value,
                    amount=order.amount,
                    price=order.avg_fill_price,
                    filled_amount=order.filled_amount,
                    filled_price=order.avg_fill_price,
                    status="filled",
                    fee=0,
                    fee_currency="USDT",
                    exchange_order_id=order.id,
                )
                db.add(trade)
                await db.commit()
                logger.info(f"Bot {bot_id}: DCA order filled at ${order.avg_fill_price}")
                
                # Send Telegram notification
                from ..services.notification_service import get_notification_service
                notification = get_notification_service()
                await notification.notify_trade_executed(
                    bot_name=bot_data.get("name", f"Bot {bot_id}"),
                    side=order.side.value,
                    amount=order.filled_amount,
                    symbol=symbol,
                    price=order.avg_fill_price,
                )
    
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
        from ..exchanges.paper import PaperExchange
        from ..services.market_service import MarketService
        from .signal_bot import SignalBot, SignalBotConfig
        
        config = bot_data["config"]
        
        # Create exchange instance
        exchange = PaperExchange(
            namespace=f"bot_{bot_id}",
            initial_balances={"USDT": config.get("budget", 10000)}
        )
        
        # Get current market price
        prices = await MarketService.get_top_prices()
        symbol = bot_data["symbol"]
        coin_symbol = symbol.replace("USDT", "").lower()
        coin_map = {"btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin"}
        coin_id = coin_map.get(coin_symbol, coin_symbol)
        
        market_price = next(
            (p["current_price"] for p in prices if p["id"] == coin_id),
            None
        )
        if not market_price:
            logger.warning(f"Bot {bot_id}: price not found for {coin_id}")
            return
        
        # Create bot instance with valid config fields
        bot_config = SignalBotConfig(
            symbol=symbol,
            coin_id=coin_id,
            signal_type=config.get("signal_type", "rsi_ema"),
            buy_threshold=config.get("buy_threshold", 0.0),
            sell_threshold=config.get("sell_threshold", 0.0),
            amount=config.get("amount", 0.001),
        )
        bot = SignalBot(exchange=exchange, config=bot_config)
        
        # Execute tick
        order = await bot.tick(market_price=market_price)
        
        # Log order to database if filled
        if order and order.status.value == "FILLED":
            async with SessionLocal() as db:
                trade = TradeOrder(
                    bot_id=bot_id,
                    user_id=bot_data["user_id"],
                    exchange="paper",
                    symbol=symbol,
                    side=order.side.value,
                    order_type=order.order_type.value,
                    amount=order.amount,
                    price=order.avg_fill_price,
                    filled_amount=order.filled_amount,
                    filled_price=order.avg_fill_price,
                    status="filled",
                    fee=0,
                    fee_currency="USDT",
                    exchange_order_id=order.id,
                )
                db.add(trade)
                await db.commit()
                logger.info(
                    f"Bot {bot_id}: Signal {order.side.value} order filled at ${order.avg_fill_price}"
                )
                
                # Send Telegram notification
                from ..services.notification_service import get_notification_service
                notification = get_notification_service()
                await notification.notify_trade_executed(
                    bot_name=bot_data.get("name", f"Bot {bot_id}"),
                    side=order.side.value,
                    amount=order.filled_amount,
                    symbol=symbol,
                    price=order.avg_fill_price,
                )
    
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("BotManager shutdown")
