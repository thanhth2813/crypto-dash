from __future__ import annotations

from fastapi import APIRouter

from ..schemas.signal import SignalResponse
from ..services.market_service import MarketService
from ..services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalResponse])
async def get_signals() -> list[SignalResponse]:
    top = await MarketService.get_top_prices(per_page=20)

    out: list[SignalResponse] = []
    for item in top:
        coin_id = str(item.get("id"))
        if not coin_id:
            continue
        symbol = str(item.get("symbol") or coin_id)
        sig = await SignalService.get_signal(coin_id=coin_id, symbol=symbol)
        out.append(SignalResponse(**sig.__dict__))

    return out


@router.get("/{coin_id}", response_model=SignalResponse)
async def get_signal(coin_id: str) -> SignalResponse:
    sig = await SignalService.get_signal(coin_id=coin_id)
    return SignalResponse(**sig.__dict__)
