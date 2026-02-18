from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from ..config import settings
from ..utils.redis import get_redis_client

logger = logging.getLogger(__name__)


class MarketService:
    @staticmethod
    async def get_top_prices(vs_currency: str = "usd", per_page: int = 20) -> list[dict[str, Any]]:
        cache_key = "market:prices"

        # cache lookup (fail-open)
        try:
            r = get_redis_client()
            cached = await r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache get failed (prices): %s", exc)

        url = f"{settings.COINGECKO_BASE_URL}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        # store cache (fail-open)
        try:
            r = get_redis_client()
            await r.setex(cache_key, 30, json.dumps(data))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache set failed (prices): %s", exc)

        return data

    @staticmethod
    async def get_ohlc(coin_id: str, days: int = 7, vs_currency: str = "usd") -> list[list[float]]:
        cache_key = f"market:ohlc:{coin_id}:{days}"

        try:
            r = get_redis_client()
            cached = await r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache get failed (ohlc): %s", exc)

        url = f"{settings.COINGECKO_BASE_URL}/coins/{coin_id}/ohlc"
        params = {"vs_currency": vs_currency, "days": days}

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        try:
            r = get_redis_client()
            await r.setex(cache_key, 300, json.dumps(data))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache set failed (ohlc): %s", exc)

        return data

    @staticmethod
    def ms_to_dt(ms: int) -> datetime:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
