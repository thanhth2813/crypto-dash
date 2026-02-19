from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..database import SessionLocal
from ..models.alert import Alert
from ..services.market_service import MarketService

logger = logging.getLogger(__name__)


async def run_once() -> None:
    """Check active alerts and mark triggered ones."""

    async with SessionLocal() as db:  # type: AsyncSession
        res = await db.execute(select(Alert).where(Alert.status == "active"))
        alerts = list(res.scalars().all())
        if not alerts:
            return

        market = await MarketService.get_top_prices()
        price_by_coin: dict[str, float] = {}
        for item in market:
            cid = str(item.get("id"))
            cp = item.get("current_price")
            if cid and cp is not None:
                price_by_coin[cid] = float(cp)

        now = datetime.now(timezone.utc)
        changed = 0
        for a in alerts:
            current = price_by_coin.get(a.coin_id)
            if current is None:
                continue

            hit = False
            if a.condition == "above" and current >= float(a.target_price):
                hit = True
            if a.condition == "below" and current <= float(a.target_price):
                hit = True

            if hit:
                a.status = "triggered"
                a.trigger_count = int(a.trigger_count or 0) + 1
                a.triggered_at = now
                changed += 1

        if changed:
            await db.commit()
            logger.info("Alert checker: triggered=%s", changed)
