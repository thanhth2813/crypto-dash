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


async def _check_limit(*, key: str, limit: int, window_seconds: int) -> tuple[bool, int | None]:
    """Return (ok, retry_after).

    Assumes Redis available; caller handles fail-open.
    """

    r = get_redis_client()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    count, ttl = await pipe.execute()

    if ttl == -1:
        await r.expire(key, window_seconds)
        ttl = window_seconds
    elif ttl == -2:
        await r.expire(key, window_seconds)
        ttl = window_seconds

    if int(count) > limit:
        retry_after = int(ttl) if ttl and int(ttl) > 0 else window_seconds
        return False, retry_after

    return True, None


async def check_login_rate_limit(*, ip: str, email: str) -> tuple[bool, int | None]:
    """2-tier login rate limit.

    - Per IP: 20/min  -> key `rl:login:ip:{ip}`
    - Per email: 5/min -> key `rl:login:email:{email}`

    Both must pass.

    Fail-open: if Redis is down/throws, return (True, None) and log warning.
    """

    try:
        ip_ok, ip_retry = await _check_limit(key=f"rl:login:ip:{ip}", limit=20, window_seconds=60)
        email_ok, email_retry = await _check_limit(key=f"rl:login:email:{email}", limit=5, window_seconds=60)

        if not ip_ok or not email_ok:
            retry = max(ip_retry or 0, email_retry or 0) or 60
            return False, retry

        return True, None

    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis rate limit check failed (fail-open): %s", exc)
        return True, None
