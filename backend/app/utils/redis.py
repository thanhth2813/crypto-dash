from __future__ import annotations

import logging

import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def check_login_rate_limit(
    *, ip: str, email: str, limit: int = 5, window_seconds: int = 60
) -> tuple[bool, int | None]:
    """Return (allowed, retry_after_seconds).

    Fail-open: if Redis is down/throws, return (True, None) and log warning.
    """

    key = f"rl:login:{ip}:{email}"

    try:
        r = get_redis_client()
        # Atomically increment and set TTL on first hit
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        count, ttl = await pipe.execute()

        if ttl == -1:
            # ensure expiry
            await r.expire(key, window_seconds)
            ttl = window_seconds
        elif ttl == -2:
            # key missing after pipeline? set expiry defensively
            await r.expire(key, window_seconds)
            ttl = window_seconds

        if int(count) > limit:
            retry_after = int(ttl) if ttl and int(ttl) > 0 else window_seconds
            return False, retry_after

        return True, None

    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis rate limit check failed (fail-open): %s", exc)
        return True, None
