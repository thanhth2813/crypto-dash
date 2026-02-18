from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..schemas.market import OHLCResponse, PriceResponse
from ..services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


def _parse_last_updated(value) -> datetime:
    if isinstance(value, str):
        try:
            # Coingecko returns ISO 8601 like "2026-02-18T15:00:00.123Z"
            v = value.replace("Z", "+00:00")
            return datetime.fromisoformat(v)
        except Exception:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


@router.get("/prices", response_model=list[PriceResponse])
async def prices() -> list[PriceResponse]:
    data = await MarketService.get_top_prices()

    out: list[PriceResponse] = []
    for item in data:
        if not item.get("id") or item.get("current_price") is None:
            continue

        out.append(
            PriceResponse(
                symbol=str(item.get("symbol", "")).upper(),
                coin_id=str(item.get("id")),
                price=float(item.get("current_price")),
                ts=_parse_last_updated(item.get("last_updated")),
            )
        )

    return out


@router.get("/history/{coin_id}", response_model=list[OHLCResponse])
async def history(coin_id: str, days: int = 7) -> list[OHLCResponse]:
    if days not in (1, 7, 14, 30, 90, 180, 365, 730, 3650):
        # Coingecko allows specific values; keep loose but avoid abuse
        raise HTTPException(status_code=422, detail="invalid days")

    data = await MarketService.get_ohlc(coin_id=coin_id, days=days)
    out: list[OHLCResponse] = []
    for row in data:
        # [timestamp, open, high, low, close]
        try:
            ts_ms, o, h, low_val, c = row
            out.append(
                OHLCResponse(
                    symbol=coin_id.upper(),
                    coin_id=coin_id,
                    timeframe=f"{days}d",
                    ts=MarketService.ms_to_dt(int(ts_ms)),
                    open=float(o),
                    high=float(h),
                    low=float(low_val),
                    close=float(c),
                    volume=0.0,
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail="invalid ohlc data") from exc

    return out
