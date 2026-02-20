from __future__ import annotations

import logging
from datetime import datetime, time, timezone
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal
from ..models.trade_order import TradeOrder
from ..models.trading_bot import TradingBot

logger = logging.getLogger(__name__)


def _utc_day_start(dt: datetime | None = None) -> datetime:
    now = dt or datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


class RiskManager:
    """Risk checks for live/paper trading bots."""

    async def check_order(self, bot_id: int, user_id: int, order_amount_usd: float, symbol: str) -> tuple[bool, str]:
        """Returns (allowed, reason)."""

        async with SessionLocal() as db:
            bot = await self._get_bot(db, bot_id=bot_id, user_id=user_id)
            risk = bot.risk_config or {}

            # 1) max_position_usd
            max_pos = float(risk.get("max_position_usd", 0) or 0)
            if max_pos > 0 and order_amount_usd > max_pos:
                return False, "max_position_usd exceeded"

            invested = _to_float(bot.total_invested)
            if invested <= 0:
                invested = max(order_amount_usd, 1.0)

            # 2) max_daily_loss_pct
            max_daily_loss_pct = float(risk.get("max_daily_loss_pct", 0) or 0)
            if max_daily_loss_pct > 0:
                daily_pnl = await self.get_daily_pnl(bot_id)
                daily_loss_pct = (abs(daily_pnl) / invested) * 100 if daily_pnl < 0 else 0.0
                if daily_loss_pct > max_daily_loss_pct:
                    reason = f"daily loss {daily_loss_pct:.2f}% > {max_daily_loss_pct}%"
                    await self.trigger_circuit_breaker(bot_id, reason)
                    return False, "max_daily_loss_pct hit"

            # 3) global max_total_exposure (optional)
            global_max = float(risk.get("max_total_exposure_usd", 0) or 0)
            if global_max > 0:
                exposure = await self.get_total_exposure(user_id)
                if exposure + order_amount_usd > global_max:
                    return False, "max_total_exposure exceeded"

            # 4) consecutive loss circuit breaker
            max_consecutive_losses = int(risk.get("max_consecutive_losses", 0) or 0)
            if max_consecutive_losses > 0:
                consecutive = await self._get_consecutive_losses(bot_id, max_n=max_consecutive_losses)
                if consecutive >= max_consecutive_losses:
                    reason = f"consecutive losses {consecutive} >= {max_consecutive_losses}"
                    await self.trigger_circuit_breaker(bot_id, reason)
                    return False, "max_consecutive_losses hit"

            # 5) max drawdown from peak
            max_drawdown_pct = float(risk.get("max_drawdown_pct", 0) or 0)
            if max_drawdown_pct > 0:
                dd = await self._get_drawdown_pct(bot_id)
                if dd > max_drawdown_pct:
                    await self.trigger_circuit_breaker(bot_id, f"drawdown {dd:.2f}% > {max_drawdown_pct}%")
                    return False, "max_drawdown_pct hit"

        return True, "ok"

    async def get_daily_pnl(self, bot_id: int) -> float:
        """SUM sells - buys for FILLED orders today (UTC)."""
        day_start = _utc_day_start()

        async with SessionLocal() as db:
            stmt = (
                select(
                    func.coalesce(
                        func.sum(
                            func.case(
                                (TradeOrder.side == "sell", TradeOrder.filled_price * TradeOrder.filled_amount),
                                else_=-TradeOrder.filled_price * TradeOrder.filled_amount,
                            )
                        ),
                        0,
                    )
                )
                .where(
                    TradeOrder.bot_id == bot_id,
                    TradeOrder.status == "filled",
                    TradeOrder.created_at >= day_start,
                    TradeOrder.filled_price.is_not(None),
                )
            )
            res = await db.execute(stmt)
            val = res.scalar_one()
            return _to_float(val)

    async def get_total_exposure(self, user_id: int) -> float:
        """Sum total_invested for running bots."""
        async with SessionLocal() as db:
            stmt = (
                select(func.coalesce(func.sum(TradingBot.total_invested), 0))
                .where(TradingBot.user_id == user_id, TradingBot.status == "running")
            )
            res = await db.execute(stmt)
            return _to_float(res.scalar_one())

    async def trigger_circuit_breaker(self, bot_id: int, reason: str) -> None:
        """Pause bot and stop scheduler job."""
        logger.warning("Circuit breaker bot_id=%s reason=%s", bot_id, reason)

        async with SessionLocal() as db:
            await db.execute(
                update(TradingBot)
                .where(TradingBot.id == bot_id)
                .values(status="paused")
            )
            await db.commit()

        try:
            from ..bots.manager import BotManager

            manager = BotManager.get_instance()
            await manager.stop_bot(bot_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to stop bot via BotManager: %s", exc)

    async def _get_bot(self, db: AsyncSession, *, bot_id: int, user_id: int) -> TradingBot:
        res = await db.execute(select(TradingBot).where(TradingBot.id == bot_id, TradingBot.user_id == user_id))
        bot = res.scalar_one_or_none()
        if bot is None:
            raise ValueError("bot not found")
        return bot

    async def _get_recent_filled_orders(self, bot_id: int, limit: int = 200) -> list[TradeOrder]:
        async with SessionLocal() as db:
            stmt = (
                select(TradeOrder)
                .where(TradeOrder.bot_id == bot_id, TradeOrder.status == "filled")
                .order_by(TradeOrder.created_at.asc())
                .limit(limit)
            )
            res = await db.execute(stmt)
            return list(res.scalars().all())

    async def _get_consecutive_losses(self, bot_id: int, max_n: int) -> int:
        """Count consecutive losing SELL fills using avg cost basis from previous buys."""
        orders = await self._get_recent_filled_orders(bot_id, limit=500)
        position_qty = 0.0
        avg_cost = 0.0

        consecutive = 0
        for o in orders:
            qty = _to_float(o.filled_amount or o.amount)
            px = _to_float(o.filled_price or o.price)
            if qty <= 0 or px <= 0:
                continue

            if o.side == "buy":
                # update avg cost
                new_qty = position_qty + qty
                avg_cost = ((avg_cost * position_qty) + (px * qty)) / new_qty if new_qty > 0 else px
                position_qty = new_qty

            elif o.side == "sell":
                sell_qty = min(qty, position_qty) if position_qty > 0 else qty
                profit = (px - avg_cost) * sell_qty

                if profit < 0:
                    consecutive += 1
                else:
                    consecutive = 0

                position_qty = max(0.0, position_qty - sell_qty)

        return consecutive

    async def _get_drawdown_pct(self, bot_id: int) -> float:
        """Compute drawdown from realized equity curve derived from filled trades."""
        orders = await self._get_recent_filled_orders(bot_id, limit=2000)
        position_qty = 0.0
        avg_cost = 0.0
        realized_pnl = 0.0

        peak = 0.0
        current = 0.0

        for o in orders:
            qty = _to_float(o.filled_amount or o.amount)
            px = _to_float(o.filled_price or o.price)
            if qty <= 0 or px <= 0:
                continue

            if o.side == "buy":
                new_qty = position_qty + qty
                avg_cost = ((avg_cost * position_qty) + (px * qty)) / new_qty if new_qty > 0 else px
                position_qty = new_qty

            elif o.side == "sell":
                sell_qty = min(qty, position_qty) if position_qty > 0 else qty
                realized_pnl += (px - avg_cost) * sell_qty
                position_qty = max(0.0, position_qty - sell_qty)

            current = realized_pnl
            peak = max(peak, current)

        if peak <= 0:
            return 0.0

        dd = ((peak - current) / peak) * 100
        return float(dd)
