from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass

from ..services.market_service import MarketService
from ..utils.redis import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    coin_id: str
    symbol: str
    signal: str  # BUY|SELL|HOLD
    rsi: float | None
    ema_short: float | None
    ema_long: float | None
    confidence: float | None


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = (v * k) + (ema * (1 - k))
    return float(ema)


def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta

    avg_gain = gains / period
    avg_loss = losses / period

    # Wilder smoothing
    for i in range(period + 1, len(values)):
        delta = values[i] - values[i - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _confidence(*, rsi: float | None, ema_s: float | None, ema_l: float | None) -> float | None:
    if rsi is None or ema_s is None or ema_l is None:
        return None

    # heuristic: stronger separation + more extreme RSI => higher confidence
    sep = abs(ema_s - ema_l) / max(ema_l, 1e-9)
    rsi_strength = abs(rsi - 50) / 50
    conf = min(1.0, (sep * 5) + (rsi_strength * 0.5))
    return float(round(conf, 4))


class SignalService:
    @staticmethod
    async def get_signal(coin_id: str, symbol: str | None = None) -> Signal:
        cache_key = f"signals:{coin_id}"

        # cache lookup (fail-open)
        try:
            r = get_redis_client()
            cached = await r.get(cache_key)
            if cached:
                data = json.loads(cached)
                return Signal(**data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache get failed (signals): %s", exc)

        ohlc = await MarketService.get_ohlc(coin_id=coin_id, days=7)
        closes: list[float] = []
        for row in ohlc:
            # [timestamp, open, high, low, close]
            try:
                closes.append(float(row[4]))
            except Exception:
                continue

        ema_s = _ema(closes, 9)
        ema_l = _ema(closes, 21)
        rsi = _rsi(closes, 14)

        sig = "HOLD"
        if ema_s is not None and ema_l is not None and rsi is not None:
            if ema_s > ema_l and rsi >= 55:
                sig = "BUY"
            elif ema_s < ema_l and rsi <= 45:
                sig = "SELL"

        sym = (symbol or coin_id).upper()
        conf = _confidence(rsi=rsi, ema_s=ema_s, ema_l=ema_l)

        out = Signal(
            coin_id=coin_id,
            symbol=sym,
            signal=sig,
            rsi=None if rsi is None else float(round(rsi, 4)),
            ema_short=None if ema_s is None else float(round(ema_s, 8)),
            ema_long=None if ema_l is None else float(round(ema_l, 8)),
            confidence=conf,
        )

        # cache store (TTL 5m) (fail-open)
        try:
            r = get_redis_client()
            await r.setex(cache_key, 300, json.dumps(asdict(out)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache set failed (signals): %s", exc)

        return out
